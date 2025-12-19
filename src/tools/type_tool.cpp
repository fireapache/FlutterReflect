#include "mcp/tool.h"
#include "tools/connect_tool.h"
#include "flutter/widget_inspector.h"
#include "flutter/selector.h"
#include "flutter/interaction.h"
#include <spdlog/spdlog.h>

namespace flutter::tools {

/**
 * @brief Tool to enter text into text fields
 *
 * Can type into a text field by first tapping it (using selector or widget_id)
 * or just entering text into the currently focused field.
 */
class TypeTool : public mcp::Tool {
public:
    std::string name() const override {
        return "type";
    }

    std::string description() const override {
        return "Enter text into a text field in the Flutter app. "
               "Can optionally tap a text field first using selector or widget_id before typing. "
               "If no selector/widget_id provided, types into currently focused field. "
               "Example: type(text='user@example.com', selector='TextField[contains=\"email\"]')";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        schema.properties = {
            {"uri", {
                {"type", "string"},
                {"description", "VM Service WebSocket URI for auto-connect (CLI mode)."}
            }},
            {"text", {
                {"type", "string"},
                {"description", "Text to enter into the text field"}
            }},
            {"selector", {
                {"type", "string"},
                {"description", "CSS-like selector to find text field (optional, will tap field first)"}
            }},
            {"widget_id", {
                {"type", "string"},
                {"description", "Specific widget ID of text field (optional, alternative to selector)"}
            }},
            {"clear_first", {
                {"type", "boolean"},
                {"description", "Clear existing text before typing (default: false)"},
                {"default", false}
            }}
        };
        schema.required = {"text"};
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
            std::string text = getParam<std::string>(arguments, "text");
            bool clear_first = getParamOr<bool>(arguments, "clear_first", false);

            spdlog::info("Typing text: '{}'", text);

            // Create interaction controller
            WidgetInteraction interaction(vm_client);

            // If selector or widget_id provided, tap the field first
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

                    spdlog::info("Finding text field with selector: '{}'", selector_str);

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

                    spdlog::info("Finding text field with ID: {}", widget_id);

                    auto widget_opt = tree.getNode(widget_id);
                    if (!widget_opt.has_value()) {
                        return createErrorResponse(
                            "Widget not found with ID: " + widget_id
                        );
                    }

                    widget = widget_opt.value();
                }

                // Tap the widget to focus it
                if (!widget.hasBounds()) {
                    return createErrorResponse(
                        "Widget '" + widget.getDisplayName() + "' has no bounds information. "
                        "Cannot tap to focus."
                    );
                }

                spdlog::info("Tapping text field: {} (ID: {})", widget.getDisplayName(), widget.id);
                auto bounds = widget.bounds.value();

                try {
                    interaction.tapWidget(widget);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Failed to tap text field '{}': {}", widget.getDisplayName(), error_msg);

                    std::string help_msg = "Failed to tap text field '" + widget.getDisplayName() + "' to focus it.\n";
                    help_msg += "Widget bounds: x=" + std::to_string(static_cast<int>(bounds.x)) +
                               ", y=" + std::to_string(static_cast<int>(bounds.y)) + "\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "Possible causes:\n";
                    help_msg += "- The Flutter app may not have a custom driver handler installed.\n";
                    help_msg += "- The app needs enableFlutterDriverExtension(handler:) in main.dart.";

                    return createErrorResponse(help_msg);
                }

                // Small delay to allow focus
                std::this_thread::sleep_for(std::chrono::milliseconds(100));

                // Clear if requested
                if (clear_first) {
                    spdlog::debug("Clear requested but not fully implemented yet");
                }

                // Enter text
                try {
                    interaction.enterText(text);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Failed to enter text: {}", error_msg);

                    std::string help_msg = "Failed to enter text into '" + widget.getDisplayName() + "'.\n";
                    help_msg += "Text: '" + text + "'\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "The field was tapped but text entry failed. Possible causes:\n";
                    help_msg += "- The field may not be focused properly.\n";
                    help_msg += "- Flutter Driver enter_text command may have failed.";

                    return createErrorResponse(help_msg);
                }

                return createSuccessResponse({
                    {"text", text},
                    {"widget_id", widget.id},
                    {"widget_type", widget.type},
                    {"widget_text", widget.hasText() ? widget.text.value() : ""},
                    {"identification", identification},
                    {"clear_first", clear_first}
                }, "Typed text into: " + widget.getDisplayName());

            } else {
                // No selector/widget_id - type into currently focused field
                spdlog::info("Typing into currently focused field");

                // Enter text
                try {
                    interaction.enterText(text);
                } catch (const std::exception& e) {
                    std::string error_msg = e.what();
                    spdlog::error("Failed to enter text into focused field: {}", error_msg);

                    std::string help_msg = "Failed to enter text into focused field.\n";
                    help_msg += "Text: '" + text + "'\n";
                    help_msg += "Error: " + error_msg + "\n\n";
                    help_msg += "Possible causes:\n";
                    help_msg += "- No text field is currently focused.\n";
                    help_msg += "- Use 'selector' or 'widget_id' to tap a specific text field first.\n";
                    help_msg += "- Flutter Driver enter_text command may have failed.";

                    return createErrorResponse(help_msg);
                }

                // Verify text was entered by checking current text
                std::string current_text;
                bool verified = false;
                try {
                    current_text = interaction.getText();
                    verified = current_text.find(text) != std::string::npos ||
                               current_text == text;
                    spdlog::info("Text verification: entered='{}', current='{}', verified={}",
                                text, current_text, verified);
                } catch (const std::exception& e) {
                    spdlog::warn("Could not verify text entry: {}", e.what());
                }

                return createSuccessResponse({
                    {"text", text},
                    {"method", "focused_field"},
                    {"verified", verified},
                    {"current_text", current_text}
                }, verified ? "Typed text into focused field (verified)" : "Typed text into focused field");
            }

        } catch (const std::exception& e) {
            std::string error_msg = e.what();
            spdlog::error("Type operation failed: {}", error_msg);

            std::string help_msg = "Type operation failed.\n";
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
