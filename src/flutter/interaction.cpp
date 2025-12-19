#include "flutter/interaction.h"
#include <spdlog/spdlog.h>
#include <thread>
#include <chrono>

namespace flutter {

WidgetInteraction::WidgetInteraction(std::shared_ptr<VMServiceClient> client)
    : vm_client_(client) {
    if (!vm_client_ || !vm_client_->isConnected()) {
        throw std::runtime_error("VM Service client is not connected");
    }

    // Get main isolate ID
    isolate_id_ = vm_client_->getMainIsolateId();
    spdlog::debug("WidgetInteraction initialized with isolate: {}", isolate_id_);

    // Ensure driver is enabled
    ensureDriverEnabled();
}

void WidgetInteraction::tap(double x, double y) {
    spdlog::info("Tapping at ({}, {})", x, y);

    // Use the custom handler method for coordinate-based taps
    // This sends a tapAt command to the Flutter app's driver handler
    // which injects PointerDownEvent/PointerUpEvent via GestureBinding
    tapAt(x, y);
}

void WidgetInteraction::tapBounds(const WidgetBounds& bounds) {
    if (!bounds.isValid()) {
        throw std::runtime_error("Invalid widget bounds for tap");
    }

    // Tap center of bounds
    double center_x = bounds.x + bounds.width / 2.0;
    double center_y = bounds.y + bounds.height / 2.0;

    tap(center_x, center_y);
}

void WidgetInteraction::tapWidget(const WidgetNode& node) {
    if (!node.hasBounds()) {
        throw std::runtime_error("Widget '" + node.getDisplayName() + "' has no bounds information");
    }

    tapBounds(node.bounds.value());
}

void WidgetInteraction::enterText(const std::string& text) {
    spdlog::info("Entering text: {}", text);

    // Flutter Driver's enter_text command types into the currently focused text field
    nlohmann::json params = {
        {"text", text}
    };

    try {
        callDriverExtension("enter_text", params);

        // Wait for any animations to settle
        waitUntilIdle();

        spdlog::debug("Text entry successful");
    } catch (const std::exception& e) {
        spdlog::error("Text entry failed: {}", e.what());
        throw;
    }
}

void WidgetInteraction::waitUntilIdle(int timeout_ms) {
    spdlog::debug("Waiting until app is idle (timeout: {}ms)", timeout_ms);

    // Flutter Driver's wait commands have complex serialization requirements.
    // For simplicity and reliability, we use a sleep-based approach with
    // reasonable defaults.
    int wait_time = std::min(timeout_ms, 500);
    std::this_thread::sleep_for(std::chrono::milliseconds(wait_time));
    spdlog::debug("Wait complete after {}ms", wait_time);
}

void WidgetInteraction::scroll(double dx, double dy, int duration_ms) {
    spdlog::info("Scrolling by ({}, {}) over {}ms", dx, dy, duration_ms);

    // Use custom handler for global scroll at screen center
    // Default to screen center (reasonable default for most Flutter apps)
    double center_x = 400.0;  // Will be overridden by scrollInBounds for widget-specific scroll
    double center_y = 400.0;

    scrollAt(center_x, center_y, dx, dy, duration_ms);
}

void WidgetInteraction::scrollInBounds(const WidgetBounds& bounds, double dx, double dy, int duration_ms) {
    if (!bounds.isValid()) {
        throw std::runtime_error("Invalid widget bounds for scroll");
    }

    // Get center point of bounds to start scroll
    double center_x = bounds.x + bounds.width / 2.0;
    double center_y = bounds.y + bounds.height / 2.0;

    spdlog::info("Scrolling in bounds at ({}, {}) by ({}, {})",
                 center_x, center_y, dx, dy);

    // Use custom handler for scroll at widget center
    scrollAt(center_x, center_y, dx, dy, duration_ms);
}

void WidgetInteraction::longPress(double x, double y, int duration_ms) {
    spdlog::info("Long pressing at ({}, {}) for {}ms", x, y, duration_ms);

    // Use custom handler for coordinate-based long press
    longPressAt(x, y, duration_ms);
}

bool WidgetInteraction::waitFor(std::function<bool()> condition_fn, int timeout_ms) {
    spdlog::debug("Waiting for condition (timeout: {}ms)", timeout_ms);

    auto start_time = std::chrono::steady_clock::now();
    const int poll_interval_ms = 100;

    while (true) {
        if (condition_fn()) {
            spdlog::debug("Condition met");
            return true;
        }

        auto elapsed = std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::steady_clock::now() - start_time
        ).count();

        if (elapsed >= timeout_ms) {
            spdlog::debug("Condition timeout after {}ms", elapsed);
            return false;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(poll_interval_ms));
    }
}

std::string WidgetInteraction::getText() {
    spdlog::debug("Getting text from focused field");

    // Note: Flutter Driver's get_text command requires a finder (ByValueKey, ByText, etc.)
    // to identify the widget from which to get text.
    // Without proper finder support, we cannot retrieve text.
    spdlog::warn("getText() requires a finder - not currently supported for focused field. "
                 "Use widget inspector to get text from specific widgets.");
    return "";
}

nlohmann::json WidgetInteraction::callDriverExtension(const std::string& command,
                                                       const nlohmann::json& params) {
    // Flutter Driver extension expects commands in this format:
    // Method: "ext.flutter.driver"
    // Params: { "isolateId": "...", "command": "tap", ...other_params }

    spdlog::debug("Calling Flutter Driver command: {}", command);

    // Build request params with command name and all other parameters at top level
    nlohmann::json request_params = {
        {"isolateId", isolate_id_},
        {"command", command}
    };

    // Merge additional params into request
    for (auto& [key, value] : params.items()) {
        request_params[key] = value;
    }

    spdlog::debug("Driver request params: {}", request_params.dump());

    try {
        auto response = vm_client_->callServiceMethod("ext.flutter.driver", request_params);

        // Check for errors in response
        if (response.contains("error")) {
            throw std::runtime_error("Driver error: " + response["error"].dump());
        }

        return response;
    } catch (const std::exception& e) {
        spdlog::error("Driver extension call failed: {}", e.what());
        throw std::runtime_error("Flutter Driver extension failed: " + std::string(e.what()) +
                               ". Ensure Flutter Driver is enabled in the app.");
    }
}

void WidgetInteraction::ensureDriverEnabled() {
    try {
        if (isDriverAvailable()) {
            spdlog::debug("Flutter Driver is available");
            return;
        }

        spdlog::warn("Flutter Driver may not be available");
    } catch (const std::exception& e) {
        spdlog::warn("Flutter Driver check failed: {}", e.what());
        // Don't throw here - let actual interaction methods fail if driver isn't available
    }
}

bool WidgetInteraction::isDriverAvailable() {
    try {
        // Use the "get_health" command to check if Flutter Driver is available
        nlohmann::json params = {
            {"isolateId", isolate_id_},
            {"command", "get_health"}
        };

        auto response = vm_client_->callServiceMethod("ext.flutter.driver", params);

        // Check if response indicates healthy status
        if (response.contains("result") && response["result"].contains("status")) {
            std::string status = response["result"]["status"].get<std::string>();
            return status == "ok";
        }

        // If we got a response without error, driver is likely available
        return !response.contains("error");
    } catch (const std::exception& e) {
        spdlog::debug("Driver availability check failed: {}", e.what());
        return false;
    }
}

// =============================================================================
// Custom Command Methods (via Flutter Driver requestData handler)
// =============================================================================

nlohmann::json WidgetInteraction::sendCustomCommand(const std::string& command_json) {
    spdlog::debug("Sending custom command via requestData: {}", command_json);

    // Flutter Driver's request_data command sends a message to the custom handler
    // registered via enableFlutterDriverExtension(handler: ...)
    nlohmann::json params = {
        {"isolateId", isolate_id_},
        {"command", "request_data"},
        {"message", command_json}
    };

    try {
        auto response = vm_client_->callServiceMethod("ext.flutter.driver", params);

        spdlog::debug("Custom command response: {}", response.dump());

        // Extract the response from the custom handler
        // The response structure is: { "result": { "response": "<json_string>" } }
        if (response.contains("result") && response["result"].contains("response")) {
            std::string response_str = response["result"]["response"].get<std::string>();
            return nlohmann::json::parse(response_str);
        }

        // Check for errors
        if (response.contains("error")) {
            throw std::runtime_error("Driver error: " + response["error"].dump());
        }

        return response;
    } catch (const nlohmann::json::exception& e) {
        spdlog::error("Failed to parse custom command response: {}", e.what());
        throw std::runtime_error("Failed to parse custom command response: " + std::string(e.what()));
    } catch (const std::exception& e) {
        spdlog::error("Custom command failed: {}", e.what());
        throw std::runtime_error("Custom command failed: " + std::string(e.what()) +
                               ". Ensure the Flutter app has a custom driver handler.");
    }
}

void WidgetInteraction::tapAt(double x, double y) {
    spdlog::info("Tapping at ({}, {}) via custom handler", x, y);

    nlohmann::json command = {
        {"command", "tapAt"},
        {"x", x},
        {"y", y}
    };

    auto result = sendCustomCommand(command.dump());

    // Check if the tap was successful
    if (result.contains("success") && result["success"].get<bool>()) {
        spdlog::info("Tap at ({}, {}) successful", x, y);
    } else {
        std::string error = result.value("error", "Unknown error");
        throw std::runtime_error("Tap failed: " + error);
    }
}

void WidgetInteraction::scrollAt(double x, double y, double dx, double dy, int duration_ms) {
    spdlog::info("Scrolling at ({}, {}) by ({}, {}) over {}ms via custom handler",
                 x, y, dx, dy, duration_ms);

    nlohmann::json command = {
        {"command", "scrollAt"},
        {"x", x},
        {"y", y},
        {"dx", dx},
        {"dy", dy},
        {"duration", duration_ms}
    };

    auto result = sendCustomCommand(command.dump());

    // Check if the scroll was successful
    if (result.contains("success") && result["success"].get<bool>()) {
        spdlog::info("Scroll at ({}, {}) successful", x, y);
    } else {
        std::string error = result.value("error", "Unknown error");
        throw std::runtime_error("Scroll failed: " + error);
    }
}

void WidgetInteraction::longPressAt(double x, double y, int duration_ms) {
    spdlog::info("Long pressing at ({}, {}) for {}ms via custom handler", x, y, duration_ms);

    nlohmann::json command = {
        {"command", "longPressAt"},
        {"x", x},
        {"y", y},
        {"duration", duration_ms}
    };

    auto result = sendCustomCommand(command.dump());

    // Check if the long press was successful
    if (result.contains("success") && result["success"].get<bool>()) {
        spdlog::info("Long press at ({}, {}) successful", x, y);
    } else {
        std::string error = result.value("error", "Unknown error");
        throw std::runtime_error("Long press failed: " + error);
    }
}

} // namespace flutter
