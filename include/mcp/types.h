#pragma once

#include <string>
#include <vector>
#include <optional>
#include <nlohmann/json.hpp>

namespace mcp {

/**
 * @brief MCP protocol version
 */
constexpr const char* MCP_VERSION = "2024-11-05";

/**
 * @brief Server information
 */
struct ServerInfo {
    std::string name;
    std::string version;
    std::optional<nlohmann::json> capabilities;

    nlohmann::json toJson() const {
        nlohmann::json j = {
            {"name", name},
            {"version", version}
        };
        if (capabilities.has_value()) {
            j["capabilities"] = capabilities.value();
        }
        return j;
    }
};

/**
 * @brief Client information
 */
struct ClientInfo {
    std::string name;
    std::string version;

    static ClientInfo fromJson(const nlohmann::json& j) {
        ClientInfo info;
        info.name = j.at("name").get<std::string>();
        info.version = j.at("version").get<std::string>();
        return info;
    }
};

/**
 * @brief Tool input schema
 */
struct ToolInputSchema {
    std::string type = "object";
    nlohmann::json properties;
    std::vector<std::string> required;

    nlohmann::json toJson() const {
        nlohmann::json j = {
            {"type", type},
            {"properties", properties}
        };
        if (!required.empty()) {
            j["required"] = required;
        }
        return j;
    }
};

/**
 * @brief Tool metadata
 */
struct ToolInfo {
    std::string name;
    std::string description;
    ToolInputSchema inputSchema;

    nlohmann::json toJson() const {
        return {
            {"name", name},
            {"description", description},
            {"inputSchema", inputSchema.toJson()}
        };
    }
};

/**
 * @brief MCP capabilities
 */
struct ServerCapabilities {
    bool tools = true;
    bool resources = false;
    bool prompts = false;
    bool logging = true;

    nlohmann::json toJson() const {
        nlohmann::json j;
        if (tools) {
            j["tools"] = nlohmann::json::object();
        }
        if (resources) {
            j["resources"] = nlohmann::json::object();
        }
        if (prompts) {
            j["prompts"] = nlohmann::json::object();
        }
        if (logging) {
            j["logging"] = nlohmann::json::object();
        }
        return j;
    }
};

/**
 * @brief Log levels for MCP logging
 */
enum class LogLevel {
    Debug,
    Info,
    Warning,
    Error
};

inline std::string logLevelToString(LogLevel level) {
    switch (level) {
        case LogLevel::Debug: return "debug";
        case LogLevel::Info: return "info";
        case LogLevel::Warning: return "warning";
        case LogLevel::Error: return "error";
        default: return "info";
    }
}

} // namespace mcp
