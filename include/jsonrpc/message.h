#pragma once

#include <string>
#include <optional>
#include <variant>
#include <nlohmann/json.hpp>

namespace jsonrpc {

/**
 * @brief JSON-RPC 2.0 error codes
 */
enum class ErrorCode : int {
    ParseError = -32700,
    InvalidRequest = -32600,
    MethodNotFound = -32601,
    InvalidParams = -32602,
    InternalError = -32603,
    // Server error range: -32000 to -32099
    ServerError = -32000
};

/**
 * @brief JSON-RPC 2.0 Error object
 */
struct Error {
    int code;
    std::string message;
    std::optional<nlohmann::json> data;

    /**
     * @brief Create error from ErrorCode enum
     */
    static Error fromCode(ErrorCode code, const std::string& message = "",
                          const std::optional<nlohmann::json>& data = std::nullopt);

    /**
     * @brief Serialize error to JSON
     */
    nlohmann::json toJson() const;

    /**
     * @brief Parse error from JSON
     */
    static Error fromJson(const nlohmann::json& j);
};

/**
 * @brief JSON-RPC 2.0 Request message
 */
struct Request {
    std::string jsonrpc = "2.0";
    std::string method;
    nlohmann::json params = nlohmann::json::object();
    std::variant<std::string, int64_t, std::nullptr_t> id = nullptr;

    /**
     * @brief Parse request from JSON string
     * @throws std::exception if parsing fails
     */
    static Request parse(const std::string& json);

    /**
     * @brief Parse request from JSON object
     * @throws std::exception if validation fails
     */
    static Request fromJson(const nlohmann::json& j);

    /**
     * @brief Serialize request to JSON string
     */
    std::string serialize() const;

    /**
     * @brief Convert request to JSON object
     */
    nlohmann::json toJson() const;

    /**
     * @brief Check if request has an ID (not a notification)
     */
    bool hasId() const;

    /**
     * @brief Get string representation of ID
     */
    std::string getIdString() const;
};

/**
 * @brief JSON-RPC 2.0 Response message
 */
struct Response {
    std::string jsonrpc = "2.0";
    std::optional<nlohmann::json> result;
    std::optional<Error> error;
    std::variant<std::string, int64_t, std::nullptr_t> id = nullptr;

    /**
     * @brief Create success response
     */
    static Response success(const nlohmann::json& result,
                           const std::variant<std::string, int64_t, std::nullptr_t>& id);

    /**
     * @brief Create error response
     */
    static Response errorResponse(const Error& error,
                                  const std::variant<std::string, int64_t, std::nullptr_t>& id);

    /**
     * @brief Serialize response to JSON string
     */
    std::string serialize() const;

    /**
     * @brief Convert response to JSON object
     */
    nlohmann::json toJson() const;

    /**
     * @brief Check if response is an error
     */
    bool isError() const;
};

/**
 * @brief JSON-RPC 2.0 Notification message (request without ID)
 */
struct Notification {
    std::string jsonrpc = "2.0";
    std::string method;
    nlohmann::json params = nlohmann::json::object();

    /**
     * @brief Serialize notification to JSON string
     */
    std::string serialize() const;

    /**
     * @brief Convert notification to JSON object
     */
    nlohmann::json toJson() const;

    /**
     * @brief Create notification from method and params
     */
    static Notification create(const std::string& method, const nlohmann::json& params = nlohmann::json::object());
};

/**
 * @brief Validate that a JSON object conforms to JSON-RPC 2.0 specification
 * @throws std::exception if validation fails
 */
void validateJsonRpc(const nlohmann::json& j);

} // namespace jsonrpc
