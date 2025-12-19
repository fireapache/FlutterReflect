#include "jsonrpc/handler.h"
#include <spdlog/spdlog.h>

namespace jsonrpc {

void MessageHandler::registerMethod(const std::string& method, MethodHandler handler) {
    methods_[method] = std::move(handler);
    spdlog::debug("Registered JSON-RPC method: {}", method);
}

void MessageHandler::unregisterMethod(const std::string& method) {
    methods_.erase(method);
    spdlog::debug("Unregistered JSON-RPC method: {}", method);
}

bool MessageHandler::hasMethod(const std::string& method) const {
    return methods_.find(method) != methods_.end();
}

Response MessageHandler::handleRequest(const Request& request) {
    spdlog::debug("Handling request: method={}, id={}", request.method, request.getIdString());

    // Check if method exists
    if (!hasMethod(request.method)) {
        spdlog::warn("Method not found: {}", request.method);
        return Response::errorResponse(
            Error::fromCode(ErrorCode::MethodNotFound,
                          "Method '" + request.method + "' not found"),
            request.id
        );
    }

    try {
        // Call the method handler
        auto handler = methods_.at(request.method);
        auto result = handler(request.params);

        spdlog::debug("Request handled successfully: method={}", request.method);
        return Response::success(result, request.id);

    } catch (const std::exception& e) {
        spdlog::error("Error handling request: method={}, error={}", request.method, e.what());
        return Response::errorResponse(
            Error::fromCode(ErrorCode::InternalError, e.what()),
            request.id
        );
    }
}

std::string MessageHandler::handleMessage(const std::string& message) {
    spdlog::debug("Received message: {}", message);

    try {
        // Parse request
        auto request = Request::parse(message);

        // If it's a notification (no ID), don't send a response
        if (!request.hasId()) {
            spdlog::debug("Received notification: method={}", request.method);
            // Still process it, but don't return a response
            if (hasMethod(request.method)) {
                try {
                    auto handler = methods_.at(request.method);
                    handler(request.params);
                } catch (const std::exception& e) {
                    spdlog::warn("Error handling notification: method={}, error={}",
                               request.method, e.what());
                }
            }
            return "";  // No response for notifications
        }

        // Handle request and return response
        auto response = handleRequest(request);
        auto response_str = response.serialize();
        spdlog::debug("Sending response: {}", response_str);
        return response_str;

    } catch (const std::exception& e) {
        // Parse error
        spdlog::error("Failed to parse message: {}", e.what());
        auto error_response = Response::errorResponse(
            Error::fromCode(ErrorCode::ParseError, e.what()),
            nullptr
        );
        return error_response.serialize();
    }
}

std::vector<std::string> MessageHandler::getRegisteredMethods() const {
    std::vector<std::string> method_names;
    method_names.reserve(methods_.size());

    for (const auto& [name, handler] : methods_) {
        method_names.push_back(name);
    }

    return method_names;
}

} // namespace jsonrpc
