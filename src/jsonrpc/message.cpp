#include "jsonrpc/message.h"
#include <stdexcept>
#include <sstream>

namespace jsonrpc {

// Error implementation
Error Error::fromCode(ErrorCode code, const std::string& message,
                      const std::optional<nlohmann::json>& data) {
    Error err;
    err.code = static_cast<int>(code);

    if (message.empty()) {
        // Default messages for standard error codes
        switch (code) {
            case ErrorCode::ParseError:
                err.message = "Parse error";
                break;
            case ErrorCode::InvalidRequest:
                err.message = "Invalid request";
                break;
            case ErrorCode::MethodNotFound:
                err.message = "Method not found";
                break;
            case ErrorCode::InvalidParams:
                err.message = "Invalid params";
                break;
            case ErrorCode::InternalError:
                err.message = "Internal error";
                break;
            default:
                err.message = "Server error";
                break;
        }
    } else {
        err.message = message;
    }

    err.data = data;
    return err;
}

nlohmann::json Error::toJson() const {
    nlohmann::json j = {
        {"code", code},
        {"message", message}
    };

    if (data.has_value()) {
        j["data"] = data.value();
    }

    return j;
}

Error Error::fromJson(const nlohmann::json& j) {
    Error err;
    err.code = j.at("code").get<int>();
    err.message = j.at("message").get<std::string>();

    if (j.contains("data")) {
        err.data = j["data"];
    }

    return err;
}

// Request implementation
Request Request::parse(const std::string& json) {
    try {
        auto j = nlohmann::json::parse(json);
        return fromJson(j);
    } catch (const std::exception& e) {
        throw std::runtime_error(std::string("Failed to parse JSON-RPC request: ") + e.what());
    }
}

Request Request::fromJson(const nlohmann::json& j) {
    validateJsonRpc(j);

    Request req;
    req.jsonrpc = j.at("jsonrpc").get<std::string>();
    req.method = j.at("method").get<std::string>();

    if (j.contains("params")) {
        req.params = j["params"];
    }

    if (j.contains("id")) {
        const auto& id_json = j["id"];
        if (id_json.is_string()) {
            req.id = id_json.get<std::string>();
        } else if (id_json.is_number_integer()) {
            req.id = id_json.get<int64_t>();
        } else if (id_json.is_null()) {
            req.id = nullptr;
        } else {
            throw std::runtime_error("Invalid id type in JSON-RPC request");
        }
    }

    return req;
}

std::string Request::serialize() const {
    return toJson().dump();
}

nlohmann::json Request::toJson() const {
    nlohmann::json j = {
        {"jsonrpc", jsonrpc},
        {"method", method}
    };

    if (!params.is_null()) {
        j["params"] = params;
    }

    // Add id based on variant type
    if (std::holds_alternative<std::string>(id)) {
        j["id"] = std::get<std::string>(id);
    } else if (std::holds_alternative<int64_t>(id)) {
        j["id"] = std::get<int64_t>(id);
    } else {
        j["id"] = nullptr;
    }

    return j;
}

bool Request::hasId() const {
    return !std::holds_alternative<std::nullptr_t>(id);
}

std::string Request::getIdString() const {
    if (std::holds_alternative<std::string>(id)) {
        return std::get<std::string>(id);
    } else if (std::holds_alternative<int64_t>(id)) {
        return std::to_string(std::get<int64_t>(id));
    } else {
        return "null";
    }
}

// Response implementation
Response Response::success(const nlohmann::json& result,
                          const std::variant<std::string, int64_t, std::nullptr_t>& id) {
    Response resp;
    resp.result = result;
    resp.id = id;
    return resp;
}

Response Response::errorResponse(const Error& error,
                                 const std::variant<std::string, int64_t, std::nullptr_t>& id) {
    Response resp;
    resp.error = error;
    resp.id = id;
    return resp;
}

std::string Response::serialize() const {
    return toJson().dump();
}

nlohmann::json Response::toJson() const {
    nlohmann::json j = {
        {"jsonrpc", jsonrpc}
    };

    if (result.has_value()) {
        j["result"] = result.value();
    }

    if (error.has_value()) {
        j["error"] = error.value().toJson();
    }

    // Add id based on variant type
    if (std::holds_alternative<std::string>(id)) {
        j["id"] = std::get<std::string>(id);
    } else if (std::holds_alternative<int64_t>(id)) {
        j["id"] = std::get<int64_t>(id);
    } else {
        j["id"] = nullptr;
    }

    return j;
}

bool Response::isError() const {
    return error.has_value();
}

// Notification implementation
std::string Notification::serialize() const {
    return toJson().dump();
}

nlohmann::json Notification::toJson() const {
    nlohmann::json j = {
        {"jsonrpc", jsonrpc},
        {"method", method}
    };

    if (!params.is_null()) {
        j["params"] = params;
    }

    return j;
}

Notification Notification::create(const std::string& method, const nlohmann::json& params) {
    Notification notif;
    notif.method = method;
    notif.params = params;
    return notif;
}

// Validation
void validateJsonRpc(const nlohmann::json& j) {
    if (!j.is_object()) {
        throw std::runtime_error("JSON-RPC message must be an object");
    }

    if (!j.contains("jsonrpc") || j["jsonrpc"] != "2.0") {
        throw std::runtime_error("JSON-RPC version must be '2.0'");
    }

    if (!j.contains("method")) {
        // Could be a response instead of request
        if (!j.contains("result") && !j.contains("error")) {
            throw std::runtime_error("JSON-RPC message must have 'method' or 'result'/'error'");
        }
    } else {
        // It's a request or notification
        if (!j["method"].is_string()) {
            throw std::runtime_error("JSON-RPC 'method' must be a string");
        }

        if (j.contains("params")) {
            if (!j["params"].is_object() && !j["params"].is_array()) {
                throw std::runtime_error("JSON-RPC 'params' must be an object or array");
            }
        }
    }
}

} // namespace jsonrpc
