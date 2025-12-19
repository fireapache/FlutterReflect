#pragma once

#include <string>
#include <memory>
#include <future>
#include <atomic>
#include <mutex>
#include <unordered_map>
#include <vector>
#include <functional>
#include <thread>
#include <nlohmann/json.hpp>

// Use asio_no_tls_client since Flutter VM Service uses ws:// (not wss://)
// This avoids requiring OpenSSL
#include <websocketpp/config/asio_no_tls_client.hpp>
#include <websocketpp/client.hpp>

namespace flutter {

/**
 * @brief Client for connecting to Flutter VM Service via WebSocket
 *
 * Implements JSON-RPC 2.0 over WebSocket for communication with
 * Flutter's Dart VM Service Protocol.
 *
 * Thread-safe: Multiple threads can call service methods concurrently.
 */
class VMServiceClient {
public:
    VMServiceClient();
    ~VMServiceClient();

    /**
     * @brief Connect to Flutter VM Service
     * @param uri WebSocket URI (e.g., "ws://127.0.0.1:8181/ws")
     * @param auth_token Optional authentication token
     * @return true if connection successful, false otherwise
     */
    bool connect(const std::string& uri, const std::string& auth_token = "");

    /**
     * @brief Disconnect from VM Service
     */
    void disconnect();

    /**
     * @brief Check if currently connected
     * @return true if connected, false otherwise
     */
    bool isConnected() const;

    /**
     * @brief Call a VM Service method (synchronous)
     * @param method Method name (e.g., "getVM", "getIsolate")
     * @param params Method parameters as JSON object
     * @return JSON result
     * @throws std::runtime_error if not connected or request fails
     */
    nlohmann::json callServiceMethod(const std::string& method,
                                     const nlohmann::json& params);

    /**
     * @brief Call a VM Service method (asynchronous)
     * @param method Method name
     * @param params Method parameters
     * @return Future containing JSON result
     */
    std::future<nlohmann::json> callServiceMethodAsync(
        const std::string& method, const nlohmann::json& params);

    /**
     * @brief Get list of all isolate IDs
     * @return Vector of isolate ID strings
     * @throws std::runtime_error if not connected
     */
    std::vector<std::string> getIsolateIds();

    /**
     * @brief Get the main isolate ID (where Flutter UI runs)
     * @return Main isolate ID string
     * @throws std::runtime_error if not connected or no isolates found
     */
    std::string getMainIsolateId();

    /**
     * @brief Get information about a specific isolate
     * @param isolate_id Isolate ID
     * @return JSON object containing isolate info
     * @throws std::runtime_error if not connected
     */
    nlohmann::json getIsolateInfo(const std::string& isolate_id);

    /**
     * @brief Subscribe to a VM Service event stream
     * @param stream_id Stream ID (e.g., "Extension", "Debug", "GC")
     * @throws std::runtime_error if not connected
     */
    void streamListen(const std::string& stream_id);

    /**
     * @brief Set callback for stream events
     * @param callback Function to call when events are received
     */
    void setEventCallback(std::function<void(const nlohmann::json&)> callback);

    /**
     * @brief Get the WebSocket URI currently connected to
     * @return URI string, empty if not connected
     */
    std::string getUri() const;

private:
    // WebSocket client (using no-TLS config for ws:// connections)
    websocketpp::client<websocketpp::config::asio_client> ws_client_;
    websocketpp::connection_hdl connection_;

    // Connection state
    std::string ws_uri_;
    std::string main_isolate_id_;
    std::atomic<bool> connected_{false};
    std::atomic<bool> running_{false};

    // Request ID management
    std::atomic<int64_t> next_request_id_{1};

    // Async request handling
    std::unordered_map<int64_t, std::promise<nlohmann::json>> pending_requests_;
    std::mutex requests_mutex_;

    // Event callback
    std::function<void(const nlohmann::json&)> event_callback_;
    std::mutex callback_mutex_;

    // Background thread for WebSocket event loop
    std::unique_ptr<std::thread> ws_thread_;

    // Internal methods
    void onMessage(const std::string& message);
    void onOpen(websocketpp::connection_hdl hdl);
    void onClose(websocketpp::connection_hdl hdl);
    void onFail(websocketpp::connection_hdl hdl);
    void runEventLoop();

    // Helper to send a JSON-RPC request and wait for response
    nlohmann::json sendRequest(const std::string& method,
                               const nlohmann::json& params,
                               int timeout_seconds = 30);
};

} // namespace flutter
