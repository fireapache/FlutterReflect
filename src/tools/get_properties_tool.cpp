#include "mcp/tool.h"
#include "tools/connect_tool.h"
#include "flutter/widget_inspector.h"
#include "flutter/selector.h"
#include <spdlog/spdlog.h>

namespace flutter::tools {

/**
 * @brief Tool to get detailed widget properties
 *
 * Uses WidgetInspector to retrieve comprehensive widget information
 * including diagnostic properties, layout info, and render details.
 */
class GetPropertiesTool : public mcp::Tool {
public:
    std::string name() const override {
        return "get_properties";
    }

    std::string description() const override {
        return "Get detailed properties of a widget in the Flutter app. "
               "Returns comprehensive information including diagnostic properties, "
               "layout information, render details, and widget bounds. "
               "Can find widget by CSS selector or widget ID. "
               "Example: get_properties(selector='Button[text=\"Login\"]')";
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
                {"description", "CSS-like selector to find widget (e.g., 'Button[text=\"Login\"]')"}
            }},
            {"widget_id", {
                {"type", "string"},
                {"description", "Specific widget ID (alternative to selector)"}
            }},
            {"include_children", {
                {"type", "boolean"},
                {"description", "Include child widget properties (default: false)"},
                {"default", false}
            }},
            {"max_depth", {
                {"type", "integer"},
                {"description", "Maximum depth for child widget properties (default: 1, only if include_children=true)"},
                {"minimum", 0},
                {"maximum", 10},
                {"default", 1}
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
            bool include_children = getParamOr<bool>(arguments, "include_children", false);
            int max_depth = getParamOr<int>(arguments, "max_depth", 1);

            // Must provide either selector or widget_id
            if (!arguments.contains("selector") && !arguments.contains("widget_id")) {
                return createErrorResponse(
                    "Must provide either 'selector' or 'widget_id' parameter"
                );
            }

            // Create widget inspector
            WidgetInspector inspector(vm_client);

            // Get widget tree to find the widget
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

                spdlog::info("Finding widget with selector: '{}'", selector_str);

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

                spdlog::info("Finding widget with ID: {}", widget_id);

                auto widget_opt = tree.getNode(widget_id);
                if (!widget_opt.has_value()) {
                    return createErrorResponse(
                        "Widget not found with ID: " + widget_id
                    );
                }

                widget = widget_opt.value();
            }

            spdlog::info("Getting properties for widget: {} (ID: {})", widget.getDisplayName(), widget.id);

            // Get detailed widget information
            nlohmann::json widget_details;
            try {
                widget_details = inspector.getWidgetDetails(widget.id);
            } catch (const std::exception& e) {
                spdlog::warn("Could not get detailed widget info: {}", e.what());
                // Continue with basic info
                widget_details = nlohmann::json::object();
            }

            // Build response with widget properties
            nlohmann::json properties = {
                {"id", widget.id},
                {"type", widget.type},
                {"description", widget.description},
                {"enabled", widget.enabled},
                {"visible", widget.visible}
            };

            if (widget.hasText()) {
                properties["text"] = widget.text.value();
            }

            if (widget.hasBounds()) {
                properties["bounds"] = widget.bounds.value().toJson();
            }

            // Add diagnostic properties
            if (!widget.properties.empty()) {
                properties["diagnostic_properties"] = widget.properties;
            }

            // Add detailed inspector info if available
            if (!widget_details.empty()) {
                properties["details"] = widget_details;
            }

            // Add children info
            properties["children_count"] = widget.children_ids.size();
            properties["children_ids"] = widget.children_ids;

            // Include children properties if requested
            if (include_children && !widget.children_ids.empty()) {
                nlohmann::json children_properties = nlohmann::json::array();

                for (const auto& child_id : widget.children_ids) {
                    auto child_opt = tree.getNode(child_id);
                    if (child_opt.has_value()) {
                        const auto& child = child_opt.value();
                        nlohmann::json child_info = {
                            {"id", child.id},
                            {"type", child.type},
                            {"enabled", child.enabled},
                            {"visible", child.visible}
                        };

                        if (child.hasText()) {
                            child_info["text"] = child.text.value();
                        }

                        if (child.hasBounds()) {
                            child_info["bounds"] = child.bounds.value().toJson();
                        }

                        if (!child.properties.empty()) {
                            child_info["diagnostic_properties"] = child.properties;
                        }

                        children_properties.push_back(child_info);
                    }

                    // Only include up to max_depth levels
                    if (static_cast<int>(children_properties.size()) >= max_depth * 10) {
                        break;
                    }
                }

                properties["children"] = children_properties;
            }

            return createSuccessResponse({
                {"widget", properties},
                {"identification", identification},
                {"include_children", include_children}
            }, "Retrieved properties for widget: " + widget.getDisplayName());

        } catch (const std::exception& e) {
            spdlog::error("Failed to get widget properties: {}", e.what());
            return createErrorResponse(
                std::string("Failed to get widget properties: ") + e.what()
            );
        }
    }
};

} // namespace flutter::tools
