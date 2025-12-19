#pragma once

#include <string>
#include <optional>
#include <nlohmann/json.hpp>

namespace flutter {

/**
 * @brief Configuration for launching a Flutter application
 */
struct LaunchConfig {
    std::string project_path;                   // Path to Flutter project directory
    std::string device_id = "windows";          // Target device (windows, chrome, edge, linux, macos)
    int vm_service_port = 0;                    // Port (0 = auto-assign)
    bool disable_auth = true;                   // Disable service authentication codes
    bool headless = false;                      // Run headless (web only)
    int startup_timeout_ms = 60000;             // Max wait for app startup (60 seconds)

    /**
     * @brief Validate configuration parameters
     * @return Error message if invalid, empty string if valid
     */
    std::string validate() const;

    /**
     * @brief Convert to JSON representation
     */
    nlohmann::json toJson() const;
};

/**
 * @brief Result of attempting to launch a Flutter application
 */
struct LaunchResult {
    bool success = false;                       // Whether launch succeeded
    std::string uri;                            // VM Service URI (ws://127.0.0.1:PORT/ws)
    int port = 0;                               // Assigned VM Service port
    int process_id = 0;                         // OS process ID of Flutter app
    std::string project_name;                   // Project name from pubspec.yaml
    std::string error;                          // Error message if failed

    /**
     * @brief Convert to JSON representation
     */
    nlohmann::json toJson() const;
};

/**
 * @brief Service for launching Flutter applications
 *
 * Manages process creation, monitoring, and VM Service URI extraction.
 * Supports multiple platforms (Windows, macOS, Linux, Web).
 */
class FlutterLauncher {
public:
    /**
     * @brief Launch a Flutter application
     *
     * Starts a Flutter application with the specified configuration and waits
     * for it to be ready (VM Service becomes available).
     *
     * @param config Launch configuration
     * @return Launch result with URI and process info, or error if failed
     *
     * @throws std::runtime_error on critical errors (not expected in normal use)
     *
     * @note This is a blocking operation that may take 5-60 seconds depending on config.
     * @note On success, the returned process_id can be used to later terminate the app.
     * @note The returned URI is valid immediately and can be used with flutter_connect.
     */
    static LaunchResult launch(const LaunchConfig& config);

    /**
     * @brief Check if Flutter CLI is available in PATH
     *
     * @return Flutter version string (e.g., "3.11.0") or empty string if not found
     */
    static std::string getFlutterVersion();

    /**
     * @brief Find Flutter executable in system PATH
     *
     * Searches PATH environment variable for flutter executable.
     * Returns full path or empty string if not found.
     *
     * @return Full path to flutter executable or empty string
     */
    static std::string findFlutterExecutable();

    /**
     * @brief Terminate a running Flutter application
     *
     * Terminates the Flutter process with the given PID gracefully.
     *
     * @param process_id OS process ID
     * @return True if termination succeeded, false otherwise
     */
    static bool terminateApp(int process_id);

    /**
     * @brief Check if a project directory is a valid Flutter project
     *
     * Verifies that the directory contains pubspec.yaml
     *
     * @param project_path Path to project directory
     * @return True if valid Flutter project, false otherwise
     */
    static bool isValidFlutterProject(const std::string& project_path);

private:
    /**
     * @brief Start flutter run process
     *
     * Spawns the flutter run process with appropriate flags and captures stdout/stderr.
     *
     * @param config Launch configuration
     * @return Process handle (implementation-specific)
     *
     * @throws std::runtime_error on process creation failure
     */
    static int startFlutterProcess(const LaunchConfig& config);

    /**
     * @brief Monitor process output for VM Service URI
     *
     * Reads process stdout/stderr looking for the VM Service URI line.
     * Includes timeout to prevent hanging if app fails to start.
     *
     * @param process_id Process ID
     * @param timeout_ms Max wait time in milliseconds
     * @return Extracted URI (e.g., "ws://127.0.0.1:8181/ws") or empty string on timeout
     */
    static std::string waitForVmServiceUri(int process_id, int timeout_ms);

    /**
     * @brief Parse Flutter console output for VM Service URI
     *
     * Extracts VM Service URI from Flutter's startup output.
     * Typical line: "A Dart VM Service on Windows is available at: http://127.0.0.1:8181/"
     *
     * @param output Console output line to parse
     * @return Extracted URI in ws:// format or empty string if not found
     */
    static std::string extractUriFromOutput(const std::string& output);

    /**
     * @brief Extract project name from pubspec.yaml
     *
     * Reads pubspec.yaml and extracts the 'name' field.
     *
     * @param project_path Path to project directory
     * @return Project name or "Unknown" if cannot be determined
     */
    static std::string extractProjectName(const std::string& project_path);

    /**
     * @brief Build flutter run command with flags
     *
     * Constructs the full command line for flutter run including all necessary flags.
     *
     * @param flutter_exe Path to flutter executable
     * @param config Launch configuration
     * @return Command line arguments as string
     */
    static std::string buildFlutterCommand(const std::string& flutter_exe,
                                          const LaunchConfig& config);
};

} // namespace flutter
