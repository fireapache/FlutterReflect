#pragma once

#include "jsonrpc/message.h"
#include <functional>
#include <unordered_map>
#include <memory>

namespace jsonrpc {

/**
 * @brief Handler function type for JSON-RPC methods
 * Takes request parameters and returns result or throws exception
 */
using MethodHandler = std::function<nlohmann::json(const nlohmann::json& params)>;

/**
 * @brief JSON-RPC message handler
 * Dispatches requests to registered method handlers
 */
class MessageHandler {
public:
    MessageHandler() = default;

    /**
     * @brief Register a method handler
     * @param method Method name
     * @param handler Handler function
     */
    void registerMethod(const std::string& method, MethodHandler handler);

    /**
     * @brief Unregister a method handler
     * @param method Method name
     */
    void unregisterMethod(const std::string& method);

    /**
     * @brief Check if a method is registered
     * @param method Method name
     */
    bool hasMethod(const std::string& method) const;

    /**
     * @brief Handle a JSON-RPC request
     * @param request The request to handle
     * @return Response object (success or error)
     */
    Response handleRequest(const Request& request);

    /**
     * @brief Handle a raw JSON-RPC message string
     * @param message JSON string containing request
     * @return Response as JSON string
     */
    std::string handleMessage(const std::string& message);

    /**
     * @brief Get list of registered methods
     */
    std::vector<std::string> getRegisteredMethods() const;

private:
    std::unordered_map<std::string, MethodHandler> methods_;
};

} // namespace jsonrpc
