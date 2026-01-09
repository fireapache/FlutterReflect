#include "mcp/tool.h"
#include "tools/connect_tool.h"
#include "flutter/widget_inspector.h"
#include "flutter/selector.h"
#include "flutter/interaction.h"
#include <spdlog/spdlog.h>
#include <cmath>

namespace flutter::tools {

/**
 * @brief Tool to scroll within widgets or the entire screen
 *
 * Can scroll by offset or within specific widget bounds.
 */
class ScrollTool : public mcp::Tool {
public:
    std::string name() const override {
        return "scroll";
    }

    std::string description() const override {
        return "Scroll in the Flutter app. "
               "Can scroll by offset (dx, dy) or within a specific scrollable widget. "
               "Positive dy scrolls down, negative scrolls up. Positive dx scrolls right, negative scrolls left. "
               "Example: scroll(dy=-100) to scroll up, or "
               "scroll(selector='ListView', dy=-200) to scroll within a ListView";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        schema.properties = {
            {"uri", {
                {"type", "string"},
                {"description", "VM Service WebSocket URI for auto-connect (CLI mode)."}
            }},
            {"dx", {
                {"type", "number"},
                {"description", "Horizontal scroll offset in pixels (positive=right, negative=left, default: 0)"},
                {"default", 0}
            }},
            {"dy", {
                {"type", "number"},
                {"description", "Vertical scroll offset in pixels (positive=down, negative=up, default: 0)"},
                {"default", 0}
            }},
            {"selector", {
                {"type", "string"},
                {"description", "CSS-like selector to find scrollable widget (optional, scrolls within that widget)"}
            }},
            {"widget_id", {
                {"type", "string"},
                {"description", "Specific widget ID of scrollable widget (optional, alternative to selector)"}
            }},
            {"duration_ms", {
                {"type", "integer"},
                {"description", "Duration of scroll animation in milliseconds (default: 200)"},
                {"minimum", 0},
                {"maximum", 5000},
                {"default", 200}
            }}
        };
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

            // Get parameters
            double dx = getParamOr<double>(arguments, "dx", 0.0);
            double dy = getParamOr<double>(arguments, "dy", 0.0);
            int duration_ms = getParamOr<int>(arguments, "duration_ms", 200);

            if (dx == 0.0 && dy == 0.0) {
                return createErrorResponse(
                    "Must provide non-zero dx or dy for scroll offset"
                );
            }

            spdlog::info("Scrolling by ({}, {}) over {}ms", dx, dy, duration_ms);

            // Create interaction controller
            WidgetInteraction interaction(vm_client);

            // Check if we should scroll within a specific widget
            if (arguments.contains("selector") || arguments.contains("widget_id")) {
                // Get widget tree
                WidgetInspector inspector(vm_client);
                WidgetTree tree = inspector.getWidgetTree(0);

                if (tree.getNodeCount() == 0) {
                    return createErrorResponse(
                        "Failed to extract widget tree. Ensure the Flutter app is running in debug mode."
                    );
                }

                WidgetNode widget;
                std::string identification;

                if (arguments.contains("selector")) {
                    std::string selector_str = getParam<std::string>(arguments, "selector");
                    identification = "selector: " + selector_str;

                    spdlog::info("Finding scrollable widget with selector: '{}'", selector_str);

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

                    widget = match.value();

                } else {
                    // widget_id provided
                    std::string widget_id = getParam<std::string>(arguments, "widget_id");
                    identification = "widget_id: " + widget_id;

                    spdlog::info("Finding scrollable widget with ID: {}", widget_id);

                    auto widget_opt = tree.getNode(widget_id);
                    if (!widget_opt.has_value()) {
                        return createErrorResponse(
                            "Widget not found with ID: " + widget_id
                        );
                    }

                    widget = widget_opt.value();
                }

                // Scroll within widget bounds
                if (!widget.hasBounds()) {
                    return createErrorResponse(
                        "Widget '" + widget.getDisplayName() + "' has no bounds information. "
                        "Cannot determine scroll location."
                    );
                }

                spdlog::info("Scrolling within widget: {} (ID: {})", widget.getDisplayName(), widget.id);
                auto bounds = widget.bounds.value();

                try {
                    interaction.scrollInBounds(bounds, dx, dy, duration_ms);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Scroll in widget '{}' failed: {}", widget.getDisplayName(), error_msg);

                    std::string help_msg = "Scroll in widget '" + widget.getDisplayName() + "' failed.\n";
                    help_msg += "Widget bounds: x=" + std::to_string(static_cast<int>(bounds.x)) +
                               ", y=" + std::to_string(static_cast<int>(bounds.y)) +
                               ", w=" + std::to_string(static_cast<int>(bounds.width)) +
                               ", h=" + std::to_string(static_cast<int>(bounds.height)) + "\n";
                    help_msg += "Scroll offset: dx=" + std::to_string(static_cast<int>(dx)) +
                               ", dy=" + std::to_string(static_cast<int>(dy)) + "\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "Possible causes:\n";
                    help_msg += "- The Flutter app may not have a custom driver handler installed.\n";
                    help_msg += "- The app needs enableFlutterDriverExtension(handler:) in main.dart.\n";
                    help_msg += "- The widget may not be scrollable.";

                    return createErrorResponse(help_msg);
                }

                return createSuccessResponse({
                    {"dx", dx},
                    {"dy", dy},
                    {"duration_ms", duration_ms},
                    {"widget_id", widget.id},
                    {"widget_type", widget.type},
                    {"bounds", bounds.toJson()},
                    {"identification", identification},
                    {"method", "widget_bounds"}
                }, "Scrolled within widget: " + widget.getDisplayName());

            } else {
                // Scroll without specific widget (global scroll, non-blocking)
                spdlog::info("Performing global scroll");

                // Perform the scroll and return immediately
                try {
                    interaction.scroll(dx, dy, duration_ms);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Global scroll failed: {}", error_msg);

                    std::string help_msg = "Global scroll failed.\n";
                    help_msg += "Scroll offset: dx=" + std::to_string(static_cast<int>(dx)) +
                               ", dy=" + std::to_string(static_cast<int>(dy)) + "\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "Possible causes:\n";
                    help_msg += "- The Flutter app may not have a custom driver handler installed.\n";
                    help_msg += "- The app needs enableFlutterDriverExtension(handler:) in main.dart.\n";
                    help_msg += "- Try using 'selector' to scroll within a specific scrollable widget.";

                    return createErrorResponse(help_msg);
                }

                // Return immediately - caller should wait and check state if needed
                return createSuccessResponse({
                    {"dx", dx},
                    {"dy", dy},
                    {"duration_ms", duration_ms},
                    {"method", "global"}
                }, "Scrolled successfully");
            }

        } catch (const std::exception& e) {
            std::string error_msg = e.what();
            spdlog::error("Scroll failed: {}", error_msg);

            std::string help_msg = "Scroll operation failed.\n";
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
