#include "flutter/instance_discovery.h"
#include "flutter/vm_service_client.h"
#include <spdlog/spdlog.h>
#include <future>
#include <thread>
#include <algorithm>
#include <regex>
#include <stdexcept>

// For simple HTTP requests (using basic socket connection)
#ifdef _WIN32
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
    #pragma comment(lib, "wsock32.lib")
#else
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #include <netdb.h>
#endif

namespace flutter {

std::vector<FlutterInstance> InstanceDiscovery::discoverInstances(
    int port_range_start,
    int port_range_end,
    int timeout_ms) {

    std::vector<FlutterInstance> instances;

    spdlog::debug("Starting discovery scan (ports {}-{})", port_range_start, port_range_end);

    // 1. Parallel port scanning using async
    std::vector<std::future<std::optional<FlutterInstance>>> futures;

    for (int port = port_range_start; port <= port_range_end; ++port) {
        futures.push_back(
            std::async(std::launch::async, [port, timeout_ms]() {
                return probePort(port, timeout_ms);
            })
        );
    }

    // 2. Collect results
    int port_num = port_range_start;
    for (auto& future : futures) {
        try {
            auto result = future.get();
            if (result) {
                instances.push_back(*result);
                spdlog::debug("Found Flutter instance on port {}", port_num);
            }
        } catch (const std::exception& e) {
            spdlog::debug("Port {} probe exception: {}", port_num, e.what());
        }
        ++port_num;
    }

    // 3. Sort by port
    std::sort(instances.begin(), instances.end(),
              [](const FlutterInstance& a, const FlutterInstance& b) {
                  return a.port < b.port;
              });

    spdlog::info("Discovery scan complete: {} instance(s) found", instances.size());

    return instances;
}

std::optional<FlutterInstance> InstanceDiscovery::probePort(int port, int timeout_ms) {
    try {
        // 1. Try HTTP GET to Observatory endpoint
        std::string response = httpGet("127.0.0.1", port, timeout_ms);

        if (response.empty()) {
            return std::nullopt;
        }

        // 2. Check if it's Flutter Observatory
        if (response.find("Dart VM") == std::string::npos &&
            response.find("Observatory") == std::string::npos &&
            response.find("Flutter") == std::string::npos) {
            return std::nullopt;
        }

        // 3. Try WebSocket connection to validate
        std::string ws_uri = "ws://127.0.0.1:" + std::to_string(port) + "/ws";
        if (!validateFlutterService(ws_uri)) {
            spdlog::debug("Port {} has Observatory but WebSocket validation failed", port);
            return std::nullopt;
        }

        // 4. Create FlutterInstance
        FlutterInstance instance;
        instance.uri = ws_uri;
        instance.port = port;
        instance.has_auth = false;
        instance.discovered_at = std::chrono::system_clock::now();
        instance.device = "Unknown";

        // 5. Try to get VM info from WebSocket connection
        try {
            auto vm_client = std::make_shared<VMServiceClient>();
            if (vm_client->connect(ws_uri, "")) {
                auto vm_info = vm_client->callServiceMethod("getVM", nlohmann::json::object());

                instance.vm_version = vm_info.value("version", "Unknown");
                instance.project_name = extractProjectName(vm_info);
                instance.device = extractDeviceType(vm_info);

                vm_client->disconnect();

                spdlog::debug("Port {} identified as: {} ({})", port, instance.project_name, instance.device);
                return instance;
            }
        } catch (const std::exception& e) {
            spdlog::debug("Port {} WebSocket query failed: {}", port, e.what());
            // Still return instance even if we can't get VM info
            instance.project_name = "Unknown";
            return instance;
        }

        return instance;

    } catch (const std::exception& e) {
        spdlog::debug("Port {} probe failed: {}", port, e.what());
        return std::nullopt;
    }
}

bool InstanceDiscovery::validateFlutterService(const std::string& uri) {
    try {
        auto vm_client = std::make_shared<VMServiceClient>();

        // Try to connect and validate it's a valid Flutter VM Service
        if (vm_client->connect(uri, "")) {
            // Try to call getVM method to verify it's a valid Flutter VM Service
            auto vm_info = vm_client->callServiceMethod("getVM", nlohmann::json::object());

            vm_client->disconnect();

            // Check if response has expected VM fields
            if (vm_info.contains("type") && vm_info.contains("name")) {
                return true;
            }
        }

        return false;

    } catch (const std::exception& e) {
        spdlog::debug("WebSocket validation failed for {}: {}", uri, e.what());
        return false;
    }
}

std::string InstanceDiscovery::httpGet(const std::string& host, int port, int timeout_ms) {
    try {
#ifdef _WIN32
        WSADATA wsa_data;
        if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
            return "";
        }

        SOCKET sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (sock == INVALID_SOCKET) {
            WSACleanup();
            return "";
        }

        // Set timeout
        unsigned long timeout = timeout_ms;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (const char*)&timeout, sizeof(timeout));
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, (const char*)&timeout, sizeof(timeout));

        // Connect
        sockaddr_in addr = {};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        inet_pton(AF_INET, host.c_str(), &addr.sin_addr);

        if (connect(sock, (sockaddr*)&addr, sizeof(addr)) != 0) {
            closesocket(sock);
            WSACleanup();
            return "";
        }

        // Send HTTP GET request
        std::string request = "GET / HTTP/1.1\r\nHost: " + host + ":" + std::to_string(port)
                            + "\r\nConnection: close\r\n\r\n";
        if (send(sock, request.c_str(), (int)request.length(), 0) == SOCKET_ERROR) {
            closesocket(sock);
            WSACleanup();
            return "";
        }

        // Receive response
        std::string response;
        char buffer[4096];
        int bytes_received;

        while ((bytes_received = recv(sock, buffer, sizeof(buffer) - 1, 0)) > 0) {
            buffer[bytes_received] = '\0';
            response += buffer;
        }

        closesocket(sock);
        WSACleanup();

        return response;

#else
        // Unix/Linux implementation
        int sock = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
        if (sock < 0) {
            return "";
        }

        // Set timeout
        struct timeval tv;
        tv.tv_sec = timeout_ms / 1000;
        tv.tv_usec = (timeout_ms % 1000) * 1000;
        setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        setsockopt(sock, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof(tv));

        // Connect
        struct sockaddr_in addr = {};
        addr.sin_family = AF_INET;
        addr.sin_port = htons(port);
        inet_pton(AF_INET, host.c_str(), &addr.sin_addr);

        if (connect(sock, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
            close(sock);
            return "";
        }

        // Send HTTP GET request
        std::string request = "GET / HTTP/1.1\r\nHost: " + host + ":" + std::to_string(port)
                            + "\r\nConnection: close\r\n\r\n";
        if (send(sock, request.c_str(), request.length(), 0) < 0) {
            close(sock);
            return "";
        }

        // Receive response
        std::string response;
        char buffer[4096];
        int bytes_received;

        while ((bytes_received = recv(sock, buffer, sizeof(buffer) - 1, 0)) > 0) {
            buffer[bytes_received] = '\0';
            response += buffer;
        }

        close(sock);

        return response;
#endif

    } catch (const std::exception& e) {
        spdlog::debug("HTTP GET to {}:{} failed: {}", host, port, e.what());
        return "";
    }
}

nlohmann::json InstanceDiscovery::parseObservatoryInfo(const std::string& html_content) {
    nlohmann::json result = nlohmann::json::object();

    // Try to extract version info from HTML
    std::regex version_regex(R"(version['\"]?\s*[=:]\s*['\"]?([^\s'\"<,]+))");
    std::smatch match;

    if (std::regex_search(html_content, match, version_regex)) {
        result["version"] = match[1].str();
    }

    // Check for device indicators
    if (html_content.find("chrome") != std::string::npos || html_content.find("Chrome") != std::string::npos) {
        result["device"] = "Chrome";
    } else if (html_content.find("firefox") != std::string::npos || html_content.find("Firefox") != std::string::npos) {
        result["device"] = "Firefox";
    } else if (html_content.find("windows") != std::string::npos) {
        result["device"] = "Windows";
    } else if (html_content.find("linux") != std::string::npos) {
        result["device"] = "Linux";
    } else if (html_content.find("darwin") != std::string::npos || html_content.find("macos") != std::string::npos) {
        result["device"] = "macOS";
    }

    return result;
}

std::string InstanceDiscovery::extractProjectName(const nlohmann::json& vm_info) {
    // Try various fields where project name might be stored
    if (vm_info.contains("name") && vm_info["name"].is_string()) {
        std::string name = vm_info["name"].get<std::string>();
        if (!name.empty() && name != "Unknown") {
            return name;
        }
    }

    if (vm_info.contains("_name") && vm_info["_name"].is_string()) {
        std::string name = vm_info["_name"].get<std::string>();
        if (!name.empty() && name != "Unknown") {
            return name;
        }
    }

    if (vm_info.contains("targetModel") && vm_info["targetModel"].is_object()) {
        auto model = vm_info["targetModel"];
        if (model.contains("name") && model["name"].is_string()) {
            std::string name = model["name"].get<std::string>();
            if (!name.empty()) {
                return name;
            }
        }
    }

    return "Unknown";
}

std::string InstanceDiscovery::extractDeviceType(const nlohmann::json& vm_info) {
    // Try to infer from operatingSystemVersion or other fields
    if (vm_info.contains("operatingSystemVersion") && vm_info["operatingSystemVersion"].is_string()) {
        std::string version = vm_info["operatingSystemVersion"].get<std::string>();

        if (version.find("Windows") != std::string::npos) {
            return "Windows";
        } else if (version.find("Linux") != std::string::npos) {
            return "Linux";
        } else if (version.find("Darwin") != std::string::npos || version.find("macOS") != std::string::npos) {
            return "macOS";
        }
    }

    // Check for web platforms
    if (vm_info.contains("targetModel")) {
        auto model = vm_info["targetModel"];
        if (model.contains("_kind") && model["_kind"].is_string()) {
            std::string kind = model["_kind"].get<std::string>();
            if (kind.find("Chrome") != std::string::npos) {
                return "Chrome";
            } else if (kind.find("Web") != std::string::npos) {
                return "Web";
            }
        }
    }

    return "Unknown";
}

} // namespace flutter
