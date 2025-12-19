#pragma once

#include "mcp/types.h"
#include "mcp/tool.h"
#include "mcp/transport.h"
#include "jsonrpc/handler.h"
#include <memory>
#include <unordered_map>
#include <atomic>

namespace mcp {

/**
 * @brief MCP Server implementation
 * Implements the Model Context Protocol server side
 */
class Server {
public:
    /**
     * @brief Construct MCP server with transport
     * @param transport Transport layer (e.g., STDIO, HTTP)
     * @param server_info Server identification information
     */
    explicit Server(std::unique_ptr<Transport> transport,
                   const ServerInfo& server_info = ServerInfo{
                       "FlutterReflect",
                       "1.0.0"
                   });

    ~Server();

    /**
     * @brief Start the MCP server
     * Begins listening for requests
     */
    void start();

    /**
     * @brief Stop the MCP server
     */
    void stop();

    /**
     * @brief Check if server is running
     */
    bool isRunning() const;

    /**
     * @brief Register a tool with the server
     * @param tool Tool instance (ownership transferred)
     */
    void registerTool(std::unique_ptr<Tool> tool);

    /**
     * @brief Unregister a tool by name
     */
    void unregisterTool(const std::string& name);

    /**
     * @brief Get list of registered tools
     */
    std::vector<ToolInfo> getTools() const;

    /**
     * @brief Send a log message to the client
     */
    void sendLog(LogLevel level, const std::string& message, const nlohmann::json& data = nullptr);

    /**
     * @brief Send a progress notification
     */
    void sendProgress(const std::string& progressToken, double progress, double total = 1.0);

private:
    ServerInfo server_info_;
    ServerCapabilities capabilities_;
    std::unique_ptr<Transport> transport_;
    jsonrpc::MessageHandler json_handler_;
    std::unordered_map<std::string, std::unique_ptr<Tool>> tools_;
    std::atomic<bool> running_;
    std::atomic<bool> initialized_;
    ClientInfo client_info_;

    // MCP protocol handlers
    nlohmann::json handleInitialize(const nlohmann::json& params);
    nlohmann::json handleToolsList(const nlohmann::json& params);
    nlohmann::json handleToolsCall(const nlohmann::json& params);
    nlohmann::json handlePing(const nlohmann::json& params);

    // Helper methods
    void registerMcpMethods();
    void processMessage(const std::string& message);
    void sendNotification(const std::string& method, const nlohmann::json& params);
};

} // namespace mcp
