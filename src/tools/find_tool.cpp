#include "mcp/tool.h"
#include "tools/connect_tool.h"
#include "flutter/widget_inspector.h"
#include "flutter/selector.h"
#include <spdlog/spdlog.h>

namespace flutter::tools {

/**
 * @brief Tool to find widgets using CSS-like selectors
 *
 * Uses the Selector engine to locate widgets in the tree.
 * Returns matching widgets with their properties and bounds.
 */
class FindTool : public mcp::Tool {
public:
    std::string name() const override {
        return "find";
    }

    std::string description() const override {
        return "Find widgets in the Flutter app using CSS-like selectors. "
               "Supports type matching (Button), text matching ([text=\"Login\"]), "
               "text contains ([contains=\"email\"]), property matching ([enabled=true]), "
               "direct child (>), and descendant selectors (space). "
               "Returns all matching widgets with their IDs, types, text, and bounds. "
               "Example: find(selector='Button[text=\"Login\"]')";
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
                {"description", "CSS-like selector to match widgets. Examples:\n"
                                "- 'Button' - Find all buttons\n"
                                "- 'Text[text=\"Login\"]' - Find Text with exact text 'Login'\n"
                                "- 'TextField[contains=\"email\"]' - Find TextField containing 'email'\n"
                                "- 'Column > Text' - Find Text that is direct child of Column\n"
                                "- 'Container Text' - Find Text anywhere inside Container\n"
                                "- 'Button[enabled=true]' - Find enabled buttons"}
            }},
            {"find_first", {
                {"type", "boolean"},
                {"description", "If true, return only the first match. If false, return all matches (default: false)"},
                {"default", false}
            }},
            {"include_properties", {
                {"type", "boolean"},
                {"description", "If true, include all diagnostic properties in results (default: false)"},
                {"default", false}
            }}
        };
        schema.required = {"selector"};
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

            // Get parameters
            std::string selector_str = getParam<std::string>(arguments, "selector");
            bool find_first = getParamOr<bool>(arguments, "find_first", false);
            bool include_properties = getParamOr<bool>(arguments, "include_properties", false);

            spdlog::info("Finding widgets with selector: '{}'", selector_str);

            // Get VM Service client
            auto vm_client = getVMServiceClient();
            if (!vm_client || !vm_client->isConnected()) {
                return createErrorResponse(
                    "Not connected to Flutter app. Use 'connect' tool first or provide 'uri' parameter."
                );
            }

            // Create widget inspector and get tree
            WidgetInspector inspector(vm_client);
            WidgetTree tree = inspector.getWidgetTree(0); // Get full tree

            if (tree.getNodeCount() == 0) {
                return createErrorResponse(
                    "Failed to extract widget tree. Ensure the Flutter app is running in debug mode."
                );
            }

            // Parse selector
            Selector selector;
            try {
                selector = Selector::parse(selector_str);
            } catch (const std::exception& e) {
                return createErrorResponse(
                    std::string("Invalid selector: ") + e.what() +
                    "\n\nSelector syntax:\n"
                    "- Type: Button, Text, TextField, etc.\n"
                    "- Text equals: [text=\"value\"]\n"
                    "- Text contains: [contains=\"value\"]\n"
                    "- Property: [enabled=true]\n"
                    "- Direct child: >\n"
                    "- Descendant: (space)"
                );
            }

            // Find matching widgets
            std::vector<WidgetNode> matches;
            if (find_first) {
                auto first_match = selector.matchFirst(tree);
                if (first_match.has_value()) {
                    matches.push_back(first_match.value());
                }
            } else {
                matches = selector.match(tree);
            }

            spdlog::info("Found {} matching widget(s)", matches.size());

            if (matches.empty()) {
                return createSuccessResponse({
                    {"matches", nlohmann::json::array()},
                    {"count", 0},
                    {"selector", selector_str}
                }, "No widgets found matching selector");
            }

            // Format results
            nlohmann::json results = nlohmann::json::array();
            for (const auto& widget : matches) {
                nlohmann::json widget_info = {
                    {"id", widget.id},
                    {"type", widget.type},
                    {"enabled", widget.enabled},
                    {"visible", widget.visible}
                };

                if (widget.hasText()) {
                    widget_info["text"] = widget.text.value();
                }

                if (widget.hasBounds()) {
                    widget_info["bounds"] = widget.bounds.value().toJson();
                }

                if (!widget.description.empty()) {
                    widget_info["description"] = widget.description;
                }

                if (include_properties && !widget.properties.empty()) {
                    widget_info["properties"] = widget.properties;
                }

                results.push_back(widget_info);
            }

            return createSuccessResponse({
                {"matches", results},
                {"count", matches.size()},
                {"selector", selector_str},
                {"find_first", find_first}
            }, find_first ? "Found matching widget" : "Found " + std::to_string(matches.size()) + " matching widget(s)");

        } catch (const std::exception& e) {
            spdlog::error("Failed to find widgets: {}", e.what());
            return createErrorResponse(
                std::string("Failed to find widgets: ") + e.what()
            );
        }
    }
};

} // namespace flutter::tools
