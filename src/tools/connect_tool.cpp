#include "mcp/tool.h"
#include "flutter/vm_service_client.h"
#include "flutter/instance_discovery.h"
#include <spdlog/spdlog.h>
#include <memory>
#include <algorithm>

namespace flutter::tools {

// Global VM Service client (singleton pattern)
// Shared across all tools to maintain connection state
static std::shared_ptr<VMServiceClient> g_vm_client;

/**
 * @brief Helper function to list project names from discovered instances
 */
static std::string listProjectNames(const std::vector<flutter::FlutterInstance>& instances) {
    if (instances.empty()) {
        return "";
    }

    std::string result;
    for (size_t i = 0; i < instances.size(); ++i) {
        if (i > 0) result += ", ";
        result += "'" + instances[i].project_name + "'";
    }
    return result;
}

/**
 * @brief Tool to connect to a Flutter application via VM Service Protocol
 *
 * Establishes WebSocket connection to Flutter app's VM Service.
 * Supports both manual URI provision and automatic discovery.
 */
class ConnectTool : public mcp::Tool {
public:
    std::string name() const override {
        return "connect";
    }

    std::string description() const override {
        return "Connect to a Flutter application via VM Service Protocol. "
               "Supports both manual URI provision and automatic discovery mode. "
               "If uri is not provided, automatically discovers running Flutter apps. "
               "Manual: connect(uri='ws://127.0.0.1:8181/ws'). "
               "Auto-discovery: connect() or connect(project_name='myapp') or connect(port=8181)";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        schema.properties = {
            {"uri", {
                {"type", "string"},
                {"description", "WebSocket URI of Flutter VM Service (optional). "
                                "If not provided, auto-discovers running instances. "
                                "Format: ws://HOST:PORT/TOKEN/ws"}
            }},
            {"auth_token", {
                {"type", "string"},
                {"description", "Authentication token for VM Service (optional). "
                                "Usually embedded in URI, but can be provided separately for security."}
            }},
            {"port", {
                {"type", "integer"},
                {"description", "Auto-discovery: connect to instance on this port (optional). "
                                "Ignored if uri is provided."},
                {"minimum", 1024},
                {"maximum", 65535}
            }},
            {"project_name", {
                {"type", "string"},
                {"description", "Auto-discovery: connect to instance with this project name (optional). "
                                "Ignored if uri is provided."}
            }},
            {"instance_index", {
                {"type", "integer"},
                {"description", "Auto-discovery: connect to instance at this index in discovered list (optional, default: 0). "
                                "Ignored if uri or other filters provided."},
                {"default", 0},
                {"minimum", 0}
            }}
        };
        return schema;
    }

    nlohmann::json execute(const nlohmann::json& arguments) override {
        try {
            std::string uri;

            // Check if uri is provided for manual connection
            if (arguments.contains("uri") && arguments["uri"].is_string() && !arguments["uri"].get<std::string>().empty()) {
                uri = arguments["uri"].get<std::string>();
                spdlog::info("Manual connection: {}", uri);
            } else {
                // Auto-discovery mode
                spdlog::info("Auto-discovery mode: searching for running Flutter instances");

                auto instances = InstanceDiscovery::discoverInstances();

                if (instances.empty()) {
                    return createErrorResponse(
                        "No running Flutter instances found. "
                        "Either start a Flutter app with 'flutter run' or use flutter_launch to launch one."
                    );
                }

                spdlog::info("Discovered {} Flutter instance(s)", instances.size());

                // Filter by project_name if provided
                if (arguments.contains("project_name")) {
                    std::string project_name = getParamOr<std::string>(arguments, "project_name", "");
                    auto it = std::find_if(instances.begin(), instances.end(),
                        [&project_name](const flutter::FlutterInstance& inst) {
                            return inst.project_name == project_name;
                        }
                    );

                    if (it != instances.end()) {
                        uri = it->uri;
                        spdlog::info("Found instance by project name: {} on port {}", project_name, it->port);
                    } else {
                        return createErrorResponse(
                            "No instance found with project name: " + project_name + ". "
                            "Available projects: " + listProjectNames(instances)
                        );
                    }
                }
                // Filter by port if provided
                else if (arguments.contains("port")) {
                    int port = getParamOr<int>(arguments, "port", 0);
                    auto it = std::find_if(instances.begin(), instances.end(),
                        [port](const flutter::FlutterInstance& inst) {
                            return inst.port == port;
                        }
                    );

                    if (it != instances.end()) {
                        uri = it->uri;
                        spdlog::info("Found instance on port {}", port);
                    } else {
                        return createErrorResponse(
                            "No instance found on port: " + std::to_string(port)
                        );
                    }
                }
                // Use instance index
                else {
                    int index = getParamOr<int>(arguments, "instance_index", 0);
                    if (index >= instances.size()) {
                        return createErrorResponse(
                            "Invalid instance index: " + std::to_string(index) +
                            " (found " + std::to_string(instances.size()) + " instance(s))"
                        );
                    }
                    uri = instances[index].uri;
                    spdlog::info("Using instance index {} on port {}", index, instances[index].port);
                }

                spdlog::info("Auto-discovered URI: {}", uri);
            }

            std::string auth_token = getParamOr<std::string>(arguments, "auth_token", "");

            spdlog::info("Attempting to connect to Flutter app: {}", uri);

            // Create or reuse client
            if (!g_vm_client) {
                g_vm_client = std::make_shared<VMServiceClient>();
                spdlog::debug("Created new VMServiceClient instance");
            }

            // Disconnect if already connected to different URI
            if (g_vm_client->isConnected()) {
                std::string current_uri = g_vm_client->getUri();
                if (current_uri != uri) {
                    spdlog::info("Already connected to {}, disconnecting first", current_uri);
                    g_vm_client->disconnect();
                } else {
                    spdlog::info("Already connected to {}", uri);

                    // Return existing connection info
                    try {
                        auto vm_info = g_vm_client->callServiceMethod("getVM", nlohmann::json::object());
                        std::string vm_name = vm_info.value("name", "Unknown");
                        std::string main_isolate = g_vm_client->getMainIsolateId();

                        return createSuccessResponse({
                            {"vm_name", vm_name},
                            {"main_isolate_id", main_isolate},
                            {"connected", true},
                            {"uri", uri},
                            {"already_connected", true}
                        }, "Already connected to Flutter app");
                    } catch (const std::exception& e) {
                        spdlog::warn("Connection exists but VM query failed: {}", e.what());
                        // Connection might be stale, proceed with reconnect
                        g_vm_client->disconnect();
                    }
                }
            }

            // Connect
            bool success = g_vm_client->connect(uri, auth_token);

            if (success) {
                spdlog::info("Successfully connected to Flutter app");

                // Get VM info
                auto vm_info = g_vm_client->callServiceMethod("getVM", nlohmann::json::object());
                std::string vm_name = vm_info.value("name", "Unknown");
                std::string vm_version = vm_info.value("version", "Unknown");
                std::string main_isolate = g_vm_client->getMainIsolateId();

                // Get isolate count
                auto isolate_ids = g_vm_client->getIsolateIds();
                int isolate_count = static_cast<int>(isolate_ids.size());

                // Get main isolate info
                auto isolate_info = g_vm_client->getIsolateInfo(main_isolate);
                std::string isolate_name = isolate_info.value("name", "Unknown");

                spdlog::info("Connected to VM: {}, Main isolate: {} ({})",
                            vm_name, main_isolate, isolate_name);

                return createSuccessResponse({
                    {"vm_name", vm_name},
                    {"vm_version", vm_version},
                    {"main_isolate_id", main_isolate},
                    {"main_isolate_name", isolate_name},
                    {"isolate_count", isolate_count},
                    {"connected", true},
                    {"uri", uri}
                }, "Successfully connected to Flutter app");
            } else {
                spdlog::error("Failed to connect to Flutter app");
                return createErrorResponse(
                    "Failed to connect to Flutter app. Verify the URI is correct and the app is running. "
                    "Common issues: (1) Wrong port, (2) Authentication token mismatch, "
                    "(3) App not running with --observatory-port flag, (4) Firewall blocking connection."
                );
            }

        } catch (const std::exception& e) {
            spdlog::error("Connection error: {}", e.what());
            return createErrorResponse(
                std::string("Connection error: ") + e.what() +
                ". Ensure Flutter app is running with VM Service enabled (use --observatory-port flag)."
            );
        }
    }
};

/**
 * @brief Tool to disconnect from the currently connected Flutter application
 *
 * Closes WebSocket connection and cleans up resources.
 */
class DisconnectTool : public mcp::Tool {
public:
    std::string name() const override {
        return "disconnect";
    }

    std::string description() const override {
        return "Disconnect from the currently connected Flutter application. "
               "Closes the VM Service WebSocket connection and cleans up resources. "
               "No parameters required.";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        // No parameters needed
        schema.properties = nlohmann::json::object();
        return schema;
    }

    nlohmann::json execute(const nlohmann::json& arguments) override {
        try {
            if (!g_vm_client || !g_vm_client->isConnected()) {
                spdlog::warn("Disconnect requested but not connected");
                return createErrorResponse(
                    "Not connected to any Flutter app. Use 'connect' first to establish a connection."
                );
            }

            std::string uri = g_vm_client->getUri();
            spdlog::info("Disconnecting from Flutter app: {}", uri);

            g_vm_client->disconnect();

            spdlog::info("Successfully disconnected");

            return createSuccessResponse({
                {"connected", false},
                {"previous_uri", uri}
            }, "Successfully disconnected from Flutter app");

        } catch (const std::exception& e) {
            spdlog::error("Disconnect error: {}", e.what());
            return createErrorResponse(
                std::string("Disconnect error: ") + e.what()
            );
        }
    }
};

/**
 * @brief Get the global VM Service client instance
 * @return Shared pointer to VM client, or nullptr if not created yet
 *
 * Used by other tools (inspection, interaction) to access the VM connection.
 */
std::shared_ptr<VMServiceClient> getVMServiceClient() {
    return g_vm_client;
}

/**
 * @brief Check if connected to a Flutter app
 * @return true if connected, false otherwise
 */
bool isConnected() {
    return g_vm_client && g_vm_client->isConnected();
}

/**
 * @brief Require connection for tools that need it
 * @throws std::runtime_error if not connected
 *
 * Helper for other tools to ensure connection exists before executing.
 */
void requireConnection() {
    if (!isConnected()) {
        throw std::runtime_error(
            "Not connected to Flutter app. Use 'connect' tool first to establish a connection."
        );
    }
}

bool ensureConnection(const std::string& uri, const std::string& auth_token) {
    if (uri.empty()) {
        return isConnected();
    }

    // Create client if needed
    if (!g_vm_client) {
        g_vm_client = std::make_shared<VMServiceClient>();
    }

    // Already connected to same URI?
    if (g_vm_client->isConnected()) {
        if (g_vm_client->getUri() == uri) {
            return true;
        }
        g_vm_client->disconnect();
    }

    // Connect
    spdlog::info("Auto-connecting to: {}", uri);
    return g_vm_client->connect(uri, auth_token);
}

} // namespace flutter::tools
