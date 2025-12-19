#pragma once

#include "mcp/types.h"
#include <nlohmann/json.hpp>
#include <string>
#include <memory>

namespace mcp {

/**
 * @brief Base class for MCP tools
 * Tools are functions that LLMs can call to perform specific actions
 */
class Tool {
public:
    virtual ~Tool() = default;

    /**
     * @brief Get tool name (must be unique)
     * Use snake_case naming convention
     */
    virtual std::string name() const = 0;

    /**
     * @brief Get tool description (shown to LLM)
     */
    virtual std::string description() const = 0;

    /**
     * @brief Get tool input schema (JSON Schema)
     */
    virtual ToolInputSchema inputSchema() const = 0;

    /**
     * @brief Execute the tool with given parameters
     * @param arguments Tool arguments matching input schema
     * @return Tool result (will be sent to LLM)
     * @throws std::exception on error
     */
    virtual nlohmann::json execute(const nlohmann::json& arguments) = 0;

    /**
     * @brief Get tool metadata (name, description, schema)
     */
    ToolInfo getInfo() const {
        return ToolInfo{name(), description(), inputSchema()};
    }

protected:
    /**
     * @brief Helper to create success response
     */
    static nlohmann::json createSuccessResponse(const nlohmann::json& data,
                                                 const std::string& message = "") {
        nlohmann::json response = {
            {"success", true},
            {"data", data}
        };
        if (!message.empty()) {
            response["message"] = message;
        }
        return response;
    }

    /**
     * @brief Helper to create error response
     */
    static nlohmann::json createErrorResponse(const std::string& error,
                                              const nlohmann::json& data = nullptr) {
        nlohmann::json response = {
            {"success", false},
            {"error", error}
        };
        if (!data.is_null()) {
            response["data"] = data;
        }
        return response;
    }

    /**
     * @brief Helper to validate required parameter exists
     * @throws std::runtime_error if parameter missing
     */
    static void requireParam(const nlohmann::json& args, const std::string& param) {
        if (!args.contains(param)) {
            throw std::runtime_error("Missing required parameter: " + param);
        }
    }

    /**
     * @brief Helper to get parameter with type checking
     * @throws std::runtime_error if parameter missing or wrong type
     */
    template<typename T>
    static T getParam(const nlohmann::json& args, const std::string& param) {
        requireParam(args, param);
        try {
            return args[param].get<T>();
        } catch (const std::exception& e) {
            throw std::runtime_error("Invalid type for parameter '" + param + "': " + e.what());
        }
    }

    /**
     * @brief Helper to get optional parameter with default value
     */
    template<typename T>
    static T getParamOr(const nlohmann::json& args, const std::string& param, T defaultValue) {
        if (!args.contains(param)) {
            return defaultValue;
        }
        try {
            return args[param].get<T>();
        } catch (const std::exception&) {
            return defaultValue;
        }
    }
};

} // namespace mcp
