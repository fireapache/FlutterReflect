#include "mcp/tool.h"
#include "tools/connect_tool.h"
#include "flutter/widget_inspector.h"
#include "flutter/selector.h"
#include "flutter/interaction.h"
#include <spdlog/spdlog.h>

namespace flutter::tools {

/**
 * @brief Tool to tap on widgets
 *
 * Can tap by selector, widget ID, or coordinates.
 */
class TapTool : public mcp::Tool {
public:
    std::string name() const override {
        return "tap";
    }

    std::string description() const override {
        return "Tap on a widget in the Flutter app. "
               "Can tap by CSS selector, widget ID, or specific coordinates. "
               "For selectors, taps the center of the first matching widget. "
               "Example: tap(selector='Button[text=\"Login\"]') or "
               "tap(x=100, y=200)";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        schema.properties = {
            {"uri", {
                {"type", "string"},
                {"description", "VM Service WebSocket URI for auto-connect (CLI mode)."}
            }},
            {"selector", {
                {"type", "string"},
                {"description", "CSS-like selector to find widget to tap (e.g., 'Button[text=\"Login\"]')"}
            }},
            {"widget_id", {
                {"type", "string"},
                {"description", "Specific widget ID to tap (alternative to selector)"}
            }},
            {"x", {
                {"type", "number"},
                {"description", "X coordinate to tap (alternative to selector/widget_id)"}
            }},
            {"y", {
                {"type", "number"},
                {"description", "Y coordinate to tap (required if x is provided)"}
            }}
        };
        // No required params - one of selector, widget_id, or (x,y) must be provided
        return schema;
    }

    nlohmann::json execute(const nlohmann::json& arguments) override {
        try {
            // Auto-connect if URI provided (CLI mode)
            std::string uri = getParamOr<std::string>(arguments, "uri", "");
            if (!uri.empty() && !ensureConnection(uri)) {
                return createErrorResponse("Failed to connect to: " + uri);
            }

            // Check connection
            requireConnection();

            auto vm_client = getVMServiceClient();
            if (!vm_client || !vm_client->isConnected()) {
                return createErrorResponse(
                    "Not connected to Flutter app. Use 'connect' tool first or provide 'uri' parameter."
                );
            }

            // Create interaction controller
            WidgetInteraction interaction(vm_client);

            // Determine tap mode
            if (arguments.contains("x") && arguments.contains("y")) {
                // Tap by coordinates
                double x = getParam<double>(arguments, "x");
                double y = getParam<double>(arguments, "y");

                spdlog::info("Tapping at coordinates ({}, {})", x, y);

                try {
                    interaction.tap(x, y);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Tap at ({}, {}) failed: {}", x, y, error_msg);

                    // Provide helpful error message
                    std::string help_msg = "Tap at coordinates (" + std::to_string(static_cast<int>(x)) +
                                          ", " + std::to_string(static_cast<int>(y)) + ") failed.\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "Possible causes:\n";
                    help_msg += "- The Flutter app may not have a custom driver handler installed.\n";
                    help_msg += "- The app needs enableFlutterDriverExtension(handler:) in main.dart.\n";
                    help_msg += "- Coordinates may be outside the app window bounds.\n";
                    help_msg += "- The app may have crashed or become unresponsive.";

                    return createErrorResponse(help_msg);
                }

                return createSuccessResponse({
                    {"x", x},
                    {"y", y},
                    {"method", "coordinates"}
                }, "Tapped at coordinates (" + std::to_string(static_cast<int>(x)) +
                   ", " + std::to_string(static_cast<int>(y)) + ")");

            } else if (arguments.contains("selector")) {
                // Tap by selector
                std::string selector_str = getParam<std::string>(arguments, "selector");

                spdlog::info("Finding widget to tap with selector: '{}'", selector_str);

                // Get widget tree
                WidgetInspector inspector(vm_client);
                WidgetTree tree = inspector.getWidgetTree(0);

                if (tree.getNodeCount() == 0) {
                    return createErrorResponse(
                        "Failed to extract widget tree. Ensure the Flutter app is running in debug mode."
                    );
                }

                // Parse and match selector
                Selector selector;
                try {
                    selector = Selector::parse(selector_str);
                } catch (const std::exception& e) {
                    return createErrorResponse(
                        std::string("Invalid selector: ") + e.what()
                    );
                }

                auto match = selector.matchFirst(tree);
                if (!match.has_value()) {
                    return createErrorResponse(
                        "No widget found matching selector: " + selector_str
                    );
                }

                const auto& widget = match.value();

                if (!widget.hasBounds()) {
                    return createErrorResponse(
                        "Widget '" + widget.getDisplayName() + "' has no bounds information. "
                        "Cannot determine tap location."
                    );
                }

                spdlog::info("Found widget: {} (ID: {})", widget.getDisplayName(), widget.id);

                auto bounds = widget.bounds.value();

                // Tap the widget (non-blocking - returns immediately)
                try {
                    interaction.tapWidget(widget);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Tap on widget '{}' failed: {}", widget.getDisplayName(), error_msg);

                    std::string help_msg = "Tap on widget '" + widget.getDisplayName() + "' failed.\n";
                    help_msg += "Widget bounds: x=" + std::to_string(static_cast<int>(bounds.x)) +
                               ", y=" + std::to_string(static_cast<int>(bounds.y)) +
                               ", w=" + std::to_string(static_cast<int>(bounds.width)) +
                               ", h=" + std::to_string(static_cast<int>(bounds.height)) + "\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "Possible causes:\n";
                    help_msg += "- The Flutter app may not have a custom driver handler installed.\n";
                    help_msg += "- The app needs enableFlutterDriverExtension(handler:) in main.dart.\n";
                    help_msg += "- The widget may be obscured or not tappable.";

                    return createErrorResponse(help_msg);
                }

                // Return immediately - caller should wait and check state if needed
                return createSuccessResponse({
                    {"widget_id", widget.id},
                    {"widget_type", widget.type},
                    {"widget_text", widget.hasText() ? widget.text.value() : ""},
                    {"bounds", bounds.toJson()},
                    {"selector", selector_str},
                    {"method", "selector"}
                }, "Tapped widget: " + widget.getDisplayName());

            } else if (arguments.contains("widget_id")) {
                // Tap by widget ID
                std::string widget_id = getParam<std::string>(arguments, "widget_id");

                spdlog::info("Finding widget to tap with ID: {}", widget_id);

                // Get widget tree
                WidgetInspector inspector(vm_client);
                WidgetTree tree = inspector.getWidgetTree(0);

                auto widget_opt = tree.getNode(widget_id);
                if (!widget_opt.has_value()) {
                    return createErrorResponse(
                        "Widget not found with ID: " + widget_id
                    );
                }

                const auto& widget = widget_opt.value();

                if (!widget.hasBounds()) {
                    return createErrorResponse(
                        "Widget '" + widget.getDisplayName() + "' has no bounds information. "
                        "Cannot determine tap location."
                    );
                }

                auto bounds = widget.bounds.value();

                // Tap the widget (non-blocking - returns immediately)
                try {
                    interaction.tapWidget(widget);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Tap on widget '{}' failed: {}", widget.getDisplayName(), error_msg);

                    std::string help_msg = "Tap on widget '" + widget.getDisplayName() + "' (ID: " + widget_id + ") failed.\n";
                    help_msg += "Widget bounds: x=" + std::to_string(static_cast<int>(bounds.x)) +
                               ", y=" + std::to_string(static_cast<int>(bounds.y)) +
                               ", w=" + std::to_string(static_cast<int>(bounds.width)) +
                               ", h=" + std::to_string(static_cast<int>(bounds.height)) + "\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "Possible causes:\n";
                    help_msg += "- The Flutter app may not have a custom driver handler installed.\n";
                    help_msg += "- The app needs enableFlutterDriverExtension(handler:) in main.dart.\n";
                    help_msg += "- The widget may be obscured or not tappable.";

                    return createErrorResponse(help_msg);
                }

                // Return immediately - caller should wait and check state if needed
                return createSuccessResponse({
                    {"widget_id", widget.id},
                    {"widget_type", widget.type},
                    {"widget_text", widget.hasText() ? widget.text.value() : ""},
                    {"bounds", bounds.toJson()},
                    {"method", "widget_id"}
                }, "Tapped widget: " + widget.getDisplayName());

            } else {
                return createErrorResponse(
                    "Must provide either 'selector', 'widget_id', or both 'x' and 'y' coordinates"
                );
            }

        } catch (const std::exception& e) {
            std::string error_msg = e.what();
            spdlog::error("Tap failed: {}", error_msg);

            std::string help_msg = "Tap operation failed.\n";
            help_msg += "Error: " + error_msg + "\n\n";
            help_msg += "If this is a connection error, ensure:\n";
            help_msg += "- The Flutter app is running in debug mode\n";
            help_msg += "- The VM Service URI is correct\n";
            help_msg += "- The app has not crashed or been closed";

            return createErrorResponse(help_msg);
        }
    }
};

} // namespace flutter::tools
