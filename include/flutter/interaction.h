#pragma once

#include "flutter/vm_service_client.h"
#include "flutter/widget_tree.h"
#include <memory>
#include <string>
#include <nlohmann/json.hpp>

namespace flutter {

/**
 * @brief Widget interaction controller using Flutter Driver protocol
 *
 * Wraps ext.flutter.driver service extensions to provide high-level
 * interaction methods like tap, text input, and scrolling.
 */
class WidgetInteraction {
public:
    /**
     * @brief Construct interaction controller with VM Service client
     * @param client Shared pointer to VM Service client (must be connected)
     */
    explicit WidgetInteraction(std::shared_ptr<VMServiceClient> client);

    /**
     * @brief Tap on a widget at specific coordinates
     * @param x X coordinate
     * @param y Y coordinate
     * @throws std::runtime_error if tap fails
     */
    void tap(double x, double y);

    /**
     * @brief Tap on a widget by its bounds
     * @param bounds Widget bounds (will tap center)
     * @throws std::runtime_error if tap fails
     */
    void tapBounds(const WidgetBounds& bounds);

    /**
     * @brief Tap on a widget node (uses its bounds)
     * @param node Widget node to tap
     * @throws std::runtime_error if widget has no bounds or tap fails
     */
    void tapWidget(const WidgetNode& node);

    /**
     * @brief Enter text into the currently focused text field
     * @param text Text to enter
     * @throws std::runtime_error if text entry fails
     */
    void enterText(const std::string& text);

    /**
     * @brief Scroll by a specific offset
     * @param dx Horizontal scroll offset (positive = right, negative = left)
     * @param dy Vertical scroll offset (positive = down, negative = up)
     * @param duration_ms Duration of scroll animation in milliseconds
     * @throws std::runtime_error if scroll fails
     */
    void scroll(double dx, double dy, int duration_ms = 200);

    /**
     * @brief Scroll within a specific widget's bounds
     * @param bounds Bounds of scrollable widget
     * @param dx Horizontal scroll offset
     * @param dy Vertical scroll offset
     * @param duration_ms Duration of scroll animation in milliseconds
     * @throws std::runtime_error if scroll fails
     */
    void scrollInBounds(const WidgetBounds& bounds, double dx, double dy, int duration_ms = 200);

    /**
     * @brief Long press at specific coordinates
     * @param x X coordinate
     * @param y Y coordinate
     * @param duration_ms Duration of press in milliseconds
     * @throws std::runtime_error if press fails
     */
    void longPress(double x, double y, int duration_ms = 500);

    /**
     * @brief Wait for a condition with timeout
     * @param condition_fn Function that returns true when condition is met
     * @param timeout_ms Timeout in milliseconds
     * @return true if condition met, false if timeout
     */
    bool waitFor(std::function<bool()> condition_fn, int timeout_ms = 5000);

    /**
     * @brief Get current text from focused text field
     * @return Current text value
     * @throws std::runtime_error if cannot get text
     */
    std::string getText();

    /**
     * @brief Wait until the Flutter app is idle (no pending frames/animations)
     * @param timeout_ms Timeout in milliseconds
     */
    void waitUntilIdle(int timeout_ms = 5000);

    // =========================================================================
    // Custom Command Methods (via Flutter Driver requestData handler)
    // These methods send commands to a custom handler in the Flutter app
    // that injects pointer events via GestureBinding.handlePointerEvent()
    // =========================================================================

    /**
     * @brief Send a custom command to the Flutter app's driver handler
     * @param command_json JSON string with command data
     * @return Response from the custom handler
     * @throws std::runtime_error if command fails
     */
    nlohmann::json sendCustomCommand(const std::string& command_json);

    /**
     * @brief Tap at specific coordinates using custom handler
     *
     * Uses GestureBinding.handlePointerEvent() on the Flutter side
     * to inject PointerDownEvent and PointerUpEvent at the coordinates.
     *
     * @param x X coordinate
     * @param y Y coordinate
     * @throws std::runtime_error if tap fails
     */
    void tapAt(double x, double y);

    /**
     * @brief Scroll at specific coordinates using custom handler
     *
     * Uses GestureBinding.handlePointerEvent() to simulate a drag gesture
     * from (x, y) to (x+dx, y+dy).
     *
     * @param x Starting X coordinate
     * @param y Starting Y coordinate
     * @param dx Horizontal scroll offset
     * @param dy Vertical scroll offset
     * @param duration_ms Duration of scroll animation
     * @throws std::runtime_error if scroll fails
     */
    void scrollAt(double x, double y, double dx, double dy, int duration_ms = 200);

    /**
     * @brief Long press at specific coordinates using custom handler
     *
     * Uses GestureBinding.handlePointerEvent() to inject PointerDownEvent,
     * wait for the specified duration, then inject PointerUpEvent.
     *
     * @param x X coordinate
     * @param y Y coordinate
     * @param duration_ms Duration of press in milliseconds
     * @throws std::runtime_error if long press fails
     */
    void longPressAt(double x, double y, int duration_ms = 500);

private:
    std::shared_ptr<VMServiceClient> vm_client_;
    std::string isolate_id_;

    /**
     * @brief Call Flutter Driver extension method
     * @param command Driver command name
     * @param params Command parameters
     * @return Response from driver
     * @throws std::runtime_error if driver call fails
     */
    nlohmann::json callDriverExtension(const std::string& command,
                                       const nlohmann::json& params);

    /**
     * @brief Enable Flutter Driver extensions if not already enabled
     */
    void ensureDriverEnabled();

    /**
     * @brief Check if Flutter Driver is available
     * @return true if driver extensions are available
     */
    bool isDriverAvailable();
};

} // namespace flutter
