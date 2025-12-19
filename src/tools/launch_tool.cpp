#include "mcp/tool.h"
#include "flutter/app_launcher.h"
#include <spdlog/spdlog.h>

namespace flutter::tools {

/**
 * @brief Tool to launch a Flutter application
 *
 * Starts a Flutter app and waits for it to be ready with VM Service available.
 * Enables autonomous app lifecycle management without user intervention.
 */
class LaunchTool : public mcp::Tool {
public:
    std::string name() const override {
        return "launch";
    }

    std::string description() const override {
        return "Launch a Flutter application and wait for VM Service to be available. "
               "Starts 'flutter run' with specified configuration and monitors output for VM Service URI. "
               "Returns the VM Service URI, process ID, and port for connecting with 'connect' tool. "
               "Example: launch(project_path='/path/to/project', device='windows')";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        schema.properties = {
            {"project_path", {
                {"type", "string"},
                {"description", "Path to Flutter project directory (must contain pubspec.yaml). "
                                "Can be absolute or relative path."}
            }},
            {"device", {
                {"type", "string"},
                {"description", "Target device ID (default: 'windows'). "
                                "Common values: windows, chrome, edge, linux, macos. "
                                "Use 'flutter devices' to list available devices."},
                {"default", "windows"},
                {"enum", nlohmann::json::array({"windows", "chrome", "edge", "linux", "macos"})}
            }},
            {"vm_service_port", {
                {"type", "integer"},
                {"description", "VM Service port (default: auto-assign). "
                                "Specify 0 to let Flutter choose an available port."},
                {"default", 0},
                {"minimum", 0},
                {"maximum", 65535}
            }},
            {"disable_auth", {
                {"type", "boolean"},
                {"description", "Disable service authentication codes (default: true). "
                                "Disabling auth makes it easier to connect but less secure."},
                {"default", true}
            }},
            {"startup_timeout", {
                {"type", "integer"},
                {"description", "Max startup wait time in seconds (default: 60). "
                                "Increase if app takes longer to compile or start."},
                {"default", 60},
                {"minimum", 5},
                {"maximum", 300}
            }}
        };
        schema.required = {"project_path"};
        return schema;
    }

    nlohmann::json execute(const nlohmann::json& arguments) override {
        try {
            // Parse configuration
            flutter::LaunchConfig config;
            config.project_path = getParam<std::string>(arguments, "project_path");
            config.device_id = getParamOr<std::string>(arguments, "device", "windows");
            config.vm_service_port = getParamOr<int>(arguments, "vm_service_port", 0);
            config.disable_auth = getParamOr<bool>(arguments, "disable_auth", true);
            config.startup_timeout_ms = getParamOr<int>(arguments, "startup_timeout", 60) * 1000;

            spdlog::info("Launching Flutter app: {} on {}", config.project_path, config.device_id);

            // Launch app
            auto result = flutter::FlutterLauncher::launch(config);

            if (!result.success) {
                return createErrorResponse(
                    "Failed to launch Flutter app: " + result.error +
                    "\n\nTroubleshooting:\n"
                    "1. Verify Flutter SDK is installed: flutter doctor\n"
                    "2. Check project_path points to a valid Flutter project with pubspec.yaml\n"
                    "3. Ensure the target device is available: flutter devices\n"
                    "4. Try building manually first: flutter run -d <device>\n"
                    "5. Check Flutter and build tool output for compilation errors\n"
                    "6. Increase startup_timeout if build is slow"
                );
            }

            return createSuccessResponse({
                {"uri", result.uri},
                {"port", result.port},
                {"process_id", result.process_id},
                {"project_name", result.project_name},
                {"device", config.device_id}
            }, "Flutter app launched successfully. Use connect(uri='" + result.uri +
               "') to connect and start interacting with the app.");

        } catch (const std::exception& e) {
            spdlog::error("Launch execution error: {}", e.what());
            return createErrorResponse(
                "Launch error: " + std::string(e.what()) +
                "\n\nMake sure Flutter SDK is installed and the project path is correct."
            );
        }
    }
};

} // namespace flutter::tools

// Export the tool for registration
namespace {
    std::unique_ptr<mcp::Tool> createLaunchTool() {
        return std::make_unique<flutter::tools::LaunchTool>();
    }
}

// Provide a function that can be called to get the tool instance
extern "C" {
    std::unique_ptr<mcp::Tool> getLaunchTool() {
        return createLaunchTool();
    }
}
