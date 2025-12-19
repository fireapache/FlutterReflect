#include "mcp/tool.h"
#include "tools/connect_tool.h"  // For getVMServiceClient()
#include "flutter/widget_inspector.h"
#include <spdlog/spdlog.h>

namespace flutter::tools {

/**
 * @brief Tool to get the widget tree from a connected Flutter application
 *
 * Extracts and formats the complete widget tree for LLM analysis.
 * Returns both human-readable text and structured JSON.
 */
class GetTreeTool : public mcp::Tool {
public:
    std::string name() const override {
        return "get_tree";
    }

    std::string description() const override {
        return "Get the complete widget tree from the connected Flutter application. "
               "Returns a hierarchical view of all widgets including their types, text content, "
               "positions, and states. Useful for understanding the UI structure. "
               "Example: get_tree(max_depth=5, format='text')";
    }

    mcp::ToolInputSchema inputSchema() const override {
        mcp::ToolInputSchema schema;
        schema.properties = {
            {"uri", {
                {"type", "string"},
                {"description", "VM Service WebSocket URI for auto-connect (CLI mode). "
                                "If provided, connects automatically before executing."}
            }},
            {"max_depth", {
                {"type", "integer"},
                {"description", "Maximum depth to traverse in the widget tree (0 = unlimited, default: 10). "
                                "Use smaller values for quick overview, larger for detailed inspection."},
                {"minimum", 0},
                {"maximum", 100},
                {"default", 10}
            }},
            {"format", {
                {"type", "string"},
                {"description", "Output format: 'text' for human-readable tree, 'json' for structured data, "
                                "'both' for both formats (default: 'text')"},
                {"enum", nlohmann::json::array({"text", "json", "both"})},
                {"default", "text"}
            }}
        };
        return schema;
    }

    nlohmann::json execute(const nlohmann::json& arguments) override {
        try {
            // Auto-connect if URI provided (CLI mode)
            std::string uri = getParamOr<std::string>(arguments, "uri", "");
            if (!uri.empty()) {
                if (!ensureConnection(uri)) {
                    return createErrorResponse("Failed to connect to: " + uri);
                }
            }

            // Check connection
            requireConnection();

            // Get parameters
            int max_depth = getParamOr<int>(arguments, "max_depth", 10);
            std::string format = getParamOr<std::string>(arguments, "format", "text");

            // Validate max_depth
            if (max_depth < 0 || max_depth > 100) {
                return createErrorResponse(
                    "Invalid max_depth. Must be between 0 and 100."
                );
            }

            // Validate format
            if (format != "text" && format != "json" && format != "both") {
                return createErrorResponse(
                    "Invalid format. Must be 'text', 'json', or 'both'."
                );
            }

            spdlog::info("Getting widget tree (max_depth={}, format={})", max_depth, format);

            // Get VM Service client
            auto vm_client = getVMServiceClient();
            if (!vm_client || !vm_client->isConnected()) {
                return createErrorResponse(
                    "Not connected to Flutter app. Use 'connect' tool first or provide 'uri' parameter."
                );
            }

            // Create widget inspector
            WidgetInspector inspector(vm_client);

            // Extract widget tree
            WidgetTree tree = inspector.getWidgetTree(max_depth);

            if (tree.getNodeCount() == 0) {
                return createErrorResponse(
                    "Failed to extract widget tree. "
                    "Ensure the Flutter app is running in debug mode with widget inspector enabled."
                );
            }

            spdlog::info("Extracted widget tree: {} widgets", tree.getNodeCount());

            // Format output based on requested format
            std::string output_text;

            if (format == "text" || format == "both") {
                output_text = tree.toText(max_depth);
            }

            if (format == "json") {
                // JSON only
                return createSuccessResponse({
                    {"format", "json"},
                    {"widget_tree", tree.toJson()},
                    {"node_count", tree.getNodeCount()},
                    {"max_depth", max_depth}
                }, "Widget tree extracted successfully");
            }

            if (format == "both") {
                // Both text and JSON
                return createSuccessResponse({
                    {"format", "both"},
                    {"text", output_text},
                    {"json", tree.toJson()},
                    {"node_count", tree.getNodeCount()},
                    {"max_depth", max_depth}
                }, "Widget tree extracted successfully");
            }

            // Text only (default)
            return createSuccessResponse({
                {"format", "text"},
                {"text", output_text},
                {"node_count", tree.getNodeCount()},
                {"max_depth", max_depth}
            }, "Widget tree extracted successfully");

        } catch (const std::exception& e) {
            spdlog::error("Failed to get widget tree: {}", e.what());
            return createErrorResponse(
                std::string("Failed to get widget tree: ") + e.what() +
                "\n\nTroubleshooting:\n"
                "1. Ensure Flutter app is running in debug mode\n"
                "2. Ensure app was started with --vm-service-port flag\n"
                "3. Verify connection with 'connect' tool first\n"
                "4. Check if widget inspector is enabled in the app"
            );
        }
    }
};

} // namespace flutter::tools
