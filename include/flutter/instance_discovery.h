#pragma once

#include <string>
#include <vector>
#include <optional>
#include <chrono>
#include <nlohmann/json.hpp>

namespace flutter {

/**
 * @brief Represents a discovered Flutter application instance
 */
struct FlutterInstance {
    std::string uri;                                    // ws://127.0.0.1:8181/ws
    int port = 0;                                       // 8181
    std::string project_name;                           // "Bookfy" (from VM info)
    std::string device;                                 // "Windows", "Chrome", etc.
    std::string vm_version;                             // Dart VM version
    bool has_auth = false;                              // Whether auth token is required
    std::string auth_token;                             // Optional auth token
    std::chrono::system_clock::time_point discovered_at; // When instance was discovered

    /**
     * @brief Convert to JSON representation
     */
    nlohmann::json toJson() const {
        auto timestamp = std::chrono::system_clock::to_time_t(discovered_at);

        return {
            {"uri", uri},
            {"port", port},
            {"project_name", project_name},
            {"device", device},
            {"vm_version", vm_version},
            {"has_auth", has_auth},
            {"discovered_at", std::string(std::ctime(&timestamp))}
        };
    }
};

/**
 * @brief Service for discovering running Flutter application instances
 *
 * Scans a range of ports for Flutter VM Service endpoints and validates them.
 * Uses HTTP probing to detect Observatory endpoints and WebSocket validation
 * to confirm Flutter VM Service availability.
 */
class InstanceDiscovery {
public:
    /**
     * @brief Scan for running Flutter app instances
     *
     * Performs parallel port scanning on the specified range, checking each
     * port for Flutter VM Service availability.
     *
     * @param port_range_start Start of port range (default: 8080)
     * @param port_range_end End of port range (default: 8200)
     * @param timeout_ms Timeout per port probe in milliseconds (default: 500)
     * @return Vector of discovered instances sorted by port number
     *
     * @throws std::exception on critical errors
     *
     * @note Empty vector is returned (not an error) when no instances are found.
     * @note Typical scan of 121 ports with 500ms timeout takes ~60 seconds.
     */
    static std::vector<FlutterInstance> discoverInstances(
        int port_range_start = 8080,
        int port_range_end = 8200,
        int timeout_ms = 500
    );

    /**
     * @brief Check if a specific port has a Flutter app
     *
     * Probes a single port with HTTP and WebSocket validation.
     *
     * @param port Port to check
     * @param timeout_ms Timeout for probe in milliseconds
     * @return Optional FlutterInstance if valid Flutter app found
     *
     * @throws std::exception on critical errors (but silently ignores probe timeouts)
     */
    static std::optional<FlutterInstance> probePort(int port, int timeout_ms = 500);

    /**
     * @brief Validate that an endpoint is a valid Flutter VM Service
     *
     * Attempts WebSocket connection and verifies it responds to VM Service protocol.
     *
     * @param uri WebSocket URI to validate (e.g., ws://127.0.0.1:8181/ws)
     * @return true if valid Flutter VM Service, false otherwise
     */
    static bool validateFlutterService(const std::string& uri);

private:
    /**
     * @brief Make HTTP GET request to Observatory endpoint
     *
     * Attempts to retrieve Observatory information from HTTP endpoint
     * to verify it's a Flutter Observatory.
     *
     * @param host Host address (typically "127.0.0.1")
     * @param port Port number
     * @param timeout_ms Timeout in milliseconds
     * @return HTTP response body or empty string on failure
     */
    static std::string httpGet(const std::string& host, int port, int timeout_ms = 500);

    /**
     * @brief Extract VM Service info from Observatory response
     *
     * Parses Observatory HTML or JSON response to extract VM information
     * like version and project name.
     *
     * @param html_content Observatory page content
     * @return Parsed VM info as JSON object
     */
    static nlohmann::json parseObservatoryInfo(const std::string& html_content);

    /**
     * @brief Extract project name from raw VM info
     *
     * Attempts to infer project name from various sources in VM info.
     * Falls back to "Unknown" if cannot be determined.
     *
     * @param vm_info Raw VM info JSON
     * @return Project name string
     */
    static std::string extractProjectName(const nlohmann::json& vm_info);

    /**
     * @brief Extract device type from VM info or Observatory response
     *
     * @param vm_info Raw VM info JSON
     * @return Device type ("Windows", "Chrome", "Linux", etc.) or "Unknown"
     */
    static std::string extractDeviceType(const nlohmann::json& vm_info);
};

} // namespace flutter
