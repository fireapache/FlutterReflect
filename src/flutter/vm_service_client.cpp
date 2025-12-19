#include "flutter/vm_service_client.h"
#include <spdlog/spdlog.h>
#include <chrono>

namespace flutter {

VMServiceClient::VMServiceClient() {
    spdlog::debug("VMServiceClient created");
}

VMServiceClient::~VMServiceClient() {
    disconnect();
}

bool VMServiceClient::connect(const std::string& uri, const std::string& auth_token) {
    if (connected_) {
        spdlog::warn("Already connected to VM Service");
        return true;
    }

    try {
        spdlog::info("Connecting to Flutter VM Service: {}", uri);

        // Initialize WebSocket client
        ws_client_.clear_access_channels(websocketpp::log::alevel::all);
        ws_client_.clear_error_channels(websocketpp::log::elevel::all);
        ws_client_.init_asio();

        // Set handlers
        ws_client_.set_message_handler([this](auto hdl, auto msg) {
            onMessage(msg->get_payload());
        });
        ws_client_.set_open_handler([this](auto hdl) { onOpen(hdl); });
        ws_client_.set_close_handler([this](auto hdl) { onClose(hdl); });
        ws_client_.set_fail_handler([this](auto hdl) { onFail(hdl); });

        // Build WebSocket URI with auth token
        std::string full_uri = uri;
        if (!auth_token.empty()) {
            full_uri += (uri.find('?') == std::string::npos ? "?" : "&");
            full_uri += "authentication_token=" + auth_token;
        }

        ws_uri_ = uri;

        // Create connection
        websocketpp::lib::error_code ec;
        auto con = ws_client_.get_connection(full_uri, ec);
        if (ec) {
            spdlog::error("Connection creation failed: {}", ec.message());
            return false;
        }

        connection_ = ws_client_.connect(con);

        // Start WebSocket event loop in background thread
        running_ = true;
        ws_thread_ = std::make_unique<std::thread>([this]() { runEventLoop(); });

        // Wait for connection (with timeout)
        auto start = std::chrono::steady_clock::now();
        while (!connected_ &&
               std::chrono::steady_clock::now() - start < std::chrono::seconds(5)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }

        if (!connected_) {
            spdlog::error("Connection timeout");
            disconnect();
            return false;
        }

        // Get main isolate
        main_isolate_id_ = getMainIsolateId();
        spdlog::info("Connected to Flutter app, main isolate: {}", main_isolate_id_);

        return true;

    } catch (const std::exception& e) {
        spdlog::error("Connection error: {}", e.what());
        disconnect();
        return false;
    }
}

void VMServiceClient::disconnect() {
    if (!connected_ && !running_) {
        return;
    }

    spdlog::info("Disconnecting from VM Service");

    connected_ = false;
    running_ = false;

    try {
        if (connection_.lock()) {
            websocketpp::lib::error_code ec;
            ws_client_.close(connection_, websocketpp::close::status::normal, "Client disconnect", ec);
            if (ec) {
                spdlog::warn("Error closing connection: {}", ec.message());
            }
        }
    } catch (const std::exception& e) {
        spdlog::warn("Exception during disconnect: {}", e.what());
    }

    // Wait for event loop thread to finish
    if (ws_thread_ && ws_thread_->joinable()) {
        ws_thread_->join();
    }
    ws_thread_.reset();

    // Clear pending requests
    {
        std::lock_guard<std::mutex> lock(requests_mutex_);
        for (auto& [id, promise] : pending_requests_) {
            try {
                promise.set_exception(std::make_exception_ptr(
                    std::runtime_error("Connection closed")));
            } catch (...) {
                // Promise already satisfied, ignore
            }
        }
        pending_requests_.clear();
    }

    main_isolate_id_.clear();
    spdlog::info("Disconnected from VM Service");
}

bool VMServiceClient::isConnected() const {
    return connected_;
}

std::string VMServiceClient::getUri() const {
    return ws_uri_;
}

nlohmann::json VMServiceClient::callServiceMethod(const std::string& method,
                                                  const nlohmann::json& params) {
    return sendRequest(method, params);
}

std::future<nlohmann::json> VMServiceClient::callServiceMethodAsync(
    const std::string& method, const nlohmann::json& params) {

    return std::async(std::launch::async, [this, method, params]() {
        return sendRequest(method, params);
    });
}

nlohmann::json VMServiceClient::sendRequest(const std::string& method,
                                            const nlohmann::json& params,
                                            int timeout_seconds) {
    if (!connected_) {
        throw std::runtime_error("Not connected to VM Service");
    }

    int64_t request_id = next_request_id_++;

    // Create promise for async result
    std::promise<nlohmann::json> promise;
    std::future<nlohmann::json> future = promise.get_future();

    {
        std::lock_guard<std::mutex> lock(requests_mutex_);
        pending_requests_[request_id] = std::move(promise);
    }

    // Build JSON-RPC request
    nlohmann::json request = {
        {"jsonrpc", "2.0"},
        {"id", request_id},
        {"method", method},
        {"params", params}
    };

    spdlog::debug("Sending request: method={}, id={}", method, request_id);

    // Send via WebSocket
    try {
        websocketpp::lib::error_code ec;
        ws_client_.send(connection_, request.dump(),
                       websocketpp::frame::opcode::text, ec);

        if (ec) {
            std::lock_guard<std::mutex> lock(requests_mutex_);
            pending_requests_.erase(request_id);
            throw std::runtime_error("Failed to send request: " + ec.message());
        }
    } catch (const std::exception& e) {
        std::lock_guard<std::mutex> lock(requests_mutex_);
        pending_requests_.erase(request_id);
        throw;
    }

    // Wait for response (with timeout)
    if (future.wait_for(std::chrono::seconds(timeout_seconds)) == std::future_status::timeout) {
        std::lock_guard<std::mutex> lock(requests_mutex_);
        pending_requests_.erase(request_id);
        throw std::runtime_error("Request timeout");
    }

    return future.get();
}

std::vector<std::string> VMServiceClient::getIsolateIds() {
    auto vm_info = callServiceMethod("getVM", nlohmann::json::object());

    std::vector<std::string> isolate_ids;
    if (vm_info.contains("isolates")) {
        for (const auto& isolate_ref : vm_info["isolates"]) {
            if (isolate_ref.contains("id")) {
                isolate_ids.push_back(isolate_ref["id"].get<std::string>());
            }
        }
    }

    return isolate_ids;
}

std::string VMServiceClient::getMainIsolateId() {
    // Get VM info
    auto vm_info = callServiceMethod("getVM", nlohmann::json::object());

    // Find main isolate
    if (vm_info.contains("isolates")) {
        for (const auto& isolate_ref : vm_info["isolates"]) {
            std::string isolate_id = isolate_ref["id"].get<std::string>();

            // Get detailed isolate info
            auto isolate = callServiceMethod("getIsolate",
                                            {{"isolateId", isolate_id}});

            // Main isolate usually has "main" in the name
            std::string name = isolate.value("name", "");
            if (name.find("main") != std::string::npos) {
                spdlog::debug("Found main isolate: {} ({})", isolate_id, name);
                return isolate_id;
            }
        }

        // Fallback: return first isolate
        if (!vm_info["isolates"].empty()) {
            std::string isolate_id = vm_info["isolates"][0]["id"].get<std::string>();
            spdlog::warn("No isolate with 'main' in name, using first isolate: {}", isolate_id);
            return isolate_id;
        }
    }

    throw std::runtime_error("No isolates found");
}

nlohmann::json VMServiceClient::getIsolateInfo(const std::string& isolate_id) {
    return callServiceMethod("getIsolate", {{"isolateId", isolate_id}});
}

void VMServiceClient::streamListen(const std::string& stream_id) {
    callServiceMethod("streamListen", {{"streamId", stream_id}});
    spdlog::debug("Subscribed to stream: {}", stream_id);
}

void VMServiceClient::setEventCallback(std::function<void(const nlohmann::json&)> callback) {
    std::lock_guard<std::mutex> lock(callback_mutex_);
    event_callback_ = std::move(callback);
}

void VMServiceClient::runEventLoop() {
    spdlog::debug("WebSocket event loop started");

    try {
        ws_client_.run();
    } catch (const std::exception& e) {
        spdlog::error("WebSocket event loop error: {}", e.what());
    }

    running_ = false;
    spdlog::debug("WebSocket event loop stopped");
}

void VMServiceClient::onMessage(const std::string& message) {
    try {
        auto json = nlohmann::json::parse(message);

        spdlog::debug("Received message: {}", message.substr(0, 200));

        // Check if it's a response to a request
        if (json.contains("id") && !json["id"].is_null()) {
            int64_t id = json["id"].get<int64_t>();

            std::lock_guard<std::mutex> lock(requests_mutex_);
            auto it = pending_requests_.find(id);
            if (it != pending_requests_.end()) {
                if (json.contains("error")) {
                    std::string error_msg = json["error"].value("message", "Unknown error");
                    spdlog::error("Request {} failed: {}", id, error_msg);
                    it->second.set_exception(std::make_exception_ptr(
                        std::runtime_error(error_msg)));
                } else {
                    spdlog::debug("Request {} succeeded", id);
                    it->second.set_value(json["result"]);
                }
                pending_requests_.erase(it);
            }
        }
        // Check if it's an event notification
        else if (json.contains("method") && json["method"] == "streamNotify") {
            std::lock_guard<std::mutex> lock(callback_mutex_);
            if (event_callback_) {
                event_callback_(json["params"]);
            }
        }

    } catch (const std::exception& e) {
        spdlog::error("Error processing message: {}", e.what());
    }
}

void VMServiceClient::onOpen(websocketpp::connection_hdl hdl) {
    connected_ = true;
    spdlog::info("WebSocket connection opened");
}

void VMServiceClient::onClose(websocketpp::connection_hdl hdl) {
    connected_ = false;
    spdlog::info("WebSocket connection closed");
}

void VMServiceClient::onFail(websocketpp::connection_hdl hdl) {
    connected_ = false;
    auto con = ws_client_.get_con_from_hdl(hdl);
    spdlog::error("WebSocket connection failed: {}",
                 con->get_ec().message());
}

} // namespace flutter
