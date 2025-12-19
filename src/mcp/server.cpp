#include "mcp/server.h"
#include "jsonrpc/message.h"
#include <spdlog/spdlog.h>
#include <thread>

namespace mcp {

Server::Server(std::unique_ptr<Transport> transport, const ServerInfo& server_info)
    : server_info_(server_info),
      transport_(std::move(transport)),
      running_(false),
      initialized_(false) {

    capabilities_.tools = true;
    capabilities_.logging = true;

    server_info_.capabilities = capabilities_.toJson();

    registerMcpMethods();

    spdlog::info("MCP Server created: {} v{}", server_info_.name, server_info_.version);
}

Server::~Server() {
    stop();
}

void Server::start() {
    if (running_) {
        spdlog::warn("Server already running");
        return;
    }

    if (!transport_->isReady()) {
        spdlog::error("Transport not ready");
        throw std::runtime_error("Transport not ready");
    }

    running_ = true;
    spdlog::info("MCP Server started");

    // Set message callback for async processing
    transport_->setMessageCallback([this](const std::string& message) {
        processMessage(message);
    });

    // Start async transport if supported (e.g., STDIO)
    if (auto* stdio = dynamic_cast<StdioTransport*>(transport_.get())) {
        stdio->startAsync();
    }

    // Main loop (can be replaced with condition variable)
    while (running_) {
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }

    spdlog::info("MCP Server stopped");
}

void Server::stop() {
    if (!running_) {
        return;
    }

    spdlog::info("Stopping MCP Server");
    running_ = false;
    transport_->close();
}

bool Server::isRunning() const {
    return running_;
}

void Server::registerTool(std::unique_ptr<Tool> tool) {
    std::string tool_name = tool->name();
    tools_[tool_name] = std::move(tool);
    spdlog::info("Registered tool: {}", tool_name);
}

void Server::unregisterTool(const std::string& name) {
    tools_.erase(name);
    spdlog::info("Unregistered tool: {}", name);
}

std::vector<ToolInfo> Server::getTools() const {
    std::vector<ToolInfo> tool_list;
    tool_list.reserve(tools_.size());

    for (const auto& [name, tool] : tools_) {
        tool_list.push_back(tool->getInfo());
    }

    return tool_list;
}

void Server::sendLog(LogLevel level, const std::string& message, const nlohmann::json& data) {
    nlohmann::json params = {
        {"level", logLevelToString(level)},
        {"logger", server_info_.name},
        {"data", message}
    };

    if (!data.is_null()) {
        params["data"] = data;
    }

    sendNotification("notifications/message", params);
}

void Server::sendProgress(const std::string& progressToken, double progress, double total) {
    nlohmann::json params = {
        {"progressToken", progressToken},
        {"progress", progress},
        {"total", total}
    };

    sendNotification("notifications/progress", params);
}

void Server::registerMcpMethods() {
    // Initialize method
    json_handler_.registerMethod("initialize", [this](const nlohmann::json& params) {
        return handleInitialize(params);
    });

    // Tools methods
    json_handler_.registerMethod("tools/list", [this](const nlohmann::json& params) {
        return handleToolsList(params);
    });

    json_handler_.registerMethod("tools/call", [this](const nlohmann::json& params) {
        return handleToolsCall(params);
    });

    // Ping (optional)
    json_handler_.registerMethod("ping", [this](const nlohmann::json& params) {
        return handlePing(params);
    });

    spdlog::debug("Registered MCP protocol methods");
}

nlohmann::json Server::handleInitialize(const nlohmann::json& params) {
    spdlog::info("Handling initialize request");

    if (initialized_) {
        throw std::runtime_error("Server already initialized");
    }

    // Extract client info
    if (params.contains("clientInfo")) {
        client_info_ = ClientInfo::fromJson(params["clientInfo"]);
        spdlog::info("Client: {} v{}", client_info_.name, client_info_.version);
    }

    // Extract protocol version
    std::string protocol_version = params.value("protocolVersion", MCP_VERSION);
    spdlog::info("Protocol version: {}", protocol_version);

    initialized_ = true;

    return {
        {"protocolVersion", MCP_VERSION},
        {"serverInfo", server_info_.toJson()},
        {"capabilities", capabilities_.toJson()}
    };
}

nlohmann::json Server::handleToolsList(const nlohmann::json& params) {
    spdlog::debug("Handling tools/list request");

    if (!initialized_) {
        throw std::runtime_error("Server not initialized");
    }

    nlohmann::json tools_array = nlohmann::json::array();

    for (const auto& tool_info : getTools()) {
        tools_array.push_back(tool_info.toJson());
    }

    return {
        {"tools", tools_array}
    };
}

nlohmann::json Server::handleToolsCall(const nlohmann::json& params) {
    if (!initialized_) {
        throw std::runtime_error("Server not initialized");
    }

    // Extract tool name and arguments
    std::string tool_name = params.at("name").get<std::string>();
    nlohmann::json arguments = params.value("arguments", nlohmann::json::object());

    spdlog::info("Calling tool: {}", tool_name);
    spdlog::debug("Tool arguments: {}", arguments.dump());

    // Find tool
    auto it = tools_.find(tool_name);
    if (it == tools_.end()) {
        throw std::runtime_error("Tool not found: " + tool_name);
    }

    // Execute tool
    try {
        auto result = it->second->execute(arguments);
        spdlog::info("Tool {} executed successfully", tool_name);

        return {
            {"content", nlohmann::json::array({
                {
                    {"type", "text"},
                    {"text", result.dump(2)}
                }
            })}
        };

    } catch (const std::exception& e) {
        spdlog::error("Tool {} execution failed: {}", tool_name, e.what());
        throw;
    }
}

nlohmann::json Server::handlePing(const nlohmann::json& params) {
    return nlohmann::json::object();  // Empty response for ping
}

void Server::processMessage(const std::string& message) {
    if (message.empty()) {
        return;
    }

    try {
        std::string response = json_handler_.handleMessage(message);

        // Send response if not empty (notifications don't get responses)
        if (!response.empty()) {
            transport_->send(response);
        }

    } catch (const std::exception& e) {
        spdlog::error("Error processing message: {}", e.what());
    }
}

void Server::sendNotification(const std::string& method, const nlohmann::json& params) {
    auto notification = jsonrpc::Notification::create(method, params);
    transport_->send(notification.serialize());
}

} // namespace mcp
