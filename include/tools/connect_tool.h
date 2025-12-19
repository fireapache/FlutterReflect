#pragma once

#include "mcp/tool.h"
#include "flutter/vm_service_client.h"
#include <memory>

namespace flutter::tools {

// Forward declarations for tool classes
class ConnectTool;
class DisconnectTool;

/**
 * @brief Get the global VM Service client instance
 * @return Shared pointer to VM client, or nullptr if not created yet
 */
std::shared_ptr<VMServiceClient> getVMServiceClient();

/**
 * @brief Check if connected to a Flutter app
 * @return true if connected, false otherwise
 */
bool isConnected();

/**
 * @brief Require connection for tools that need it
 * @throws std::runtime_error if not connected
 */
void requireConnection();

/**
 * @brief Ensure connection to a Flutter app (for CLI auto-connect)
 * @param uri VM Service WebSocket URI
 * @param auth_token Optional authentication token
 * @return true if connected successfully, false otherwise
 *
 * If already connected to the same URI, returns true without reconnecting.
 * If connected to a different URI, disconnects first then connects to new URI.
 */
bool ensureConnection(const std::string& uri, const std::string& auth_token = "");

} // namespace flutter::tools
