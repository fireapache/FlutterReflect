#include "mcp/tool.h"
#include "flutter/instance_discovery.h"
#include <spdlog/spdlog.h>

namespace flutter::tools {

/**
 * @brief Tool to discover and list running Flutter application instances
 *
 * Scans a port range for running Flutter VM Services and returns information
 * about discovered instances including URI, port, project name, and device type.
 *
 * This tool enables autonomous discovery without requiring manual URI provision.
 */
class ListInstancesTool : public mcp::Tool {
public:
    std::string name() const override {
        return "list_instances";
    }

    std::string description() const override {
        return "Discover and list all running Flutter application instances. "
               "Scans common ports (8080-8200) to find active Flutter apps with VM Service enabled. "
               "Returns instance URIs, ports, project names, and connection details. "
               "Use this to auto-discover available apps before calling 'connect'. "
               "If no instances are found, use 'launch' to start a Flutter app. "
               "Example: list_instances(port_start=8080, port_end=8200, timeout_ms=500)";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        schema.properties = {
            {"port_start", {
                {"type", "integer"},
                {"description", "Start of port range to scan (default: 8080). "
                                "Flutter apps typically run on ports 8080-8200 in debug mode."},
                {"default", 8080},
                {"minimum", 1024},
                {"maximum", 65535}
            }},
            {"port_end", {
                {"type", "integer"},
                {"description", "End of port range to scan (default: 8200). "
                                "Increase to scan more ports, decrease for faster scans."},
                {"default", 8200},
                {"minimum", 1024},
                {"maximum", 65535}
            }},
            {"timeout_ms", {
                {"type", "integer"},
                {"description", "Timeout per port probe in milliseconds (default: 500). "
                                "Shorter timeouts scan faster but may miss slow responses. "
                                "Longer timeouts are more reliable but slower."},
                {"default", 500},
                {"minimum", 100},
                {"maximum", 5000}
            }}
        };
        return schema;
    }

    nlohmann::json execute(const nlohmann::json& arguments) override {
        try {
            // Parse parameters
            int port_start = getParamOr<int>(arguments, "port_start", 8080);
            int port_end = getParamOr<int>(arguments, "port_end", 8200);
            int timeout_ms = getParamOr<int>(arguments, "timeout_ms", 500);

            // Validate parameters
            if (port_start < 1024 || port_start > 65535) {
                return createErrorResponse(
                    "Invalid port_start: " + std::to_string(port_start) +
                    ". Must be between 1024 and 65535."
                );
            }

            if (port_end < 1024 || port_end > 65535) {
                return createErrorResponse(
                    "Invalid port_end: " + std::to_string(port_end) +
                    ". Must be between 1024 and 65535."
                );
            }

            if (port_start > port_end) {
                return createErrorResponse(
                    "Invalid port range: port_start (" + std::to_string(port_start) +
                    ") must be less than or equal to port_end (" + std::to_string(port_end) + ")."
                );
            }

            if (timeout_ms < 100 || timeout_ms > 5000) {
                return createErrorResponse(
                    "Invalid timeout_ms: " + std::to_string(timeout_ms) +
                    ". Must be between 100 and 5000 milliseconds."
                );
            }

            int num_ports = port_end - port_start + 1;
            spdlog::info("Discovering Flutter instances (ports {}-{}, {}ms timeout per port)",
                        port_start, port_end, timeout_ms);

            // Perform discovery
            auto instances = InstanceDiscovery::discoverInstances(port_start, port_end, timeout_ms);

            // Build response
            nlohmann::json instances_json = nlohmann::json::array();

            for (const auto& instance : instances) {
                instances_json.push_back({
                    {"uri", instance.uri},
                    {"port", instance.port},
                    {"project_name", instance.project_name},
                    {"device", instance.device},
                    {"vm_version", instance.vm_version},
                    {"has_auth", instance.has_auth}
                });
            }

            if (instances.empty()) {
                spdlog::info("No Flutter instances discovered");

                return createSuccessResponse({
                    {"instances", instances_json},
                    {"count", 0}
                }, "No running Flutter instances found. Start a Flutter app with 'flutter run' or use flutter_launch.");
            }

            spdlog::info("Found {} Flutter instance(s)", instances.size());

            return createSuccessResponse({
                {"instances", instances_json},
                {"count", static_cast<int>(instances.size())},
                {"scan_params", {
                    {"port_start", port_start},
                    {"port_end", port_end},
                    {"timeout_ms", timeout_ms},
                    {"ports_scanned", num_ports}
                }}
            }, std::to_string(instances.size()) + " Flutter instance(s) discovered. "
               "Use connect(uri='<instance_uri>') to connect to an instance.");

        } catch (const std::exception& e) {
            spdlog::error("Discovery failed: {}", e.what());

            return createErrorResponse(
                std::string("Failed to discover Flutter instances: ") + e.what() +
                "\n\nTroubleshooting:\n"
                "1. Ensure at least one Flutter app is running with 'flutter run' in debug mode\n"
                "2. Verify the port range is correct (typically 8080-8200)\n"
                "3. Check that your firewall allows local connections on those ports\n"
                "4. Try increasing timeout_ms if running on a slow system\n"
                "5. Use flutter_launch to start a Flutter app if none are running"
            );
        }
    }
};

} // namespace flutter::tools

// Export the tool for registration
namespace {
    std::unique_ptr<mcp::Tool> createListInstancesTool() {
        return std::make_unique<flutter::tools::ListInstancesTool>();
    }
}

// Provide a function that can be called to get the tool instance
extern "C" {
    std::unique_ptr<mcp::Tool> getListInstancesTool() {
        return createListInstancesTool();
    }
}
