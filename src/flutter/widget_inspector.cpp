#include "flutter/widget_inspector.h"
#include <spdlog/spdlog.h>
#include <stdexcept>

namespace flutter {

WidgetInspector::WidgetInspector(std::shared_ptr<VMServiceClient> client)
    : vm_client_(client) {
    if (!vm_client_ || !vm_client_->isConnected()) {
        throw std::runtime_error("VM Service client must be connected");
    }

    // Get main isolate ID
    isolate_id_ = vm_client_->getMainIsolateId();
    spdlog::debug("WidgetInspector initialized for isolate: {}", isolate_id_);
}

nlohmann::json WidgetInspector::callInspectorExtension(
    const std::string& method, const nlohmann::json& params) {

    // Call Flutter inspector service extension
    // Service extensions are called directly with isolateId parameter
    std::string extension_method = "ext.flutter.inspector." + method;

    // Build parameters - must include isolateId
    nlohmann::json ext_params = params;
    ext_params["isolateId"] = isolate_id_;

    try {
        spdlog::debug("Calling service extension: {} with params: {}",
                     extension_method, ext_params.dump());
        auto response = vm_client_->callServiceMethod(extension_method, ext_params);
        spdlog::debug("Service extension response: {}", response.dump().substr(0, 200));
        return response;
    } catch (const std::exception& e) {
        spdlog::error("Inspector extension call failed: {}: {}",
                     extension_method, e.what());
        throw;
    }
}

std::string WidgetInspector::getRootWidgetId() {
    spdlog::debug("Getting root widget ID");

    try {
        // Call getRootWidget with objectGroup parameter
        nlohmann::json params = {
            {"objectGroup", "flutter-reflect"}
        };

        auto response = callInspectorExtension("getRootWidget", params);

        // The response contains a DiagnosticsNode object with valueId
        if (response.contains("result") && !response["result"].is_null()) {
            auto result = response["result"];

            // Extract valueId from the DiagnosticsNode
            if (result.contains("valueId") && !result["valueId"].is_null()) {
                std::string root_id = result["valueId"].get<std::string>();
                spdlog::debug("Root widget ID: {}", root_id);
                return root_id;
            }
        }

        throw std::runtime_error("Root widget ID (valueId) not found in response");

    } catch (const std::exception& e) {
        spdlog::error("Failed to get root widget: {}", e.what());
        throw std::runtime_error("Failed to get root widget. "
                               "Ensure Flutter app is running with widget inspector enabled.");
    }
}

nlohmann::json WidgetInspector::getWidgetDetails(const std::string& widget_id) {
    spdlog::debug("Getting widget details for: {}", widget_id);

    nlohmann::json params = {
        {"objectId", widget_id}
    };

    return callInspectorExtension("getDetails", params);
}

nlohmann::json WidgetInspector::getWidgetSubtree(const std::string& widget_id, int depth) {
    spdlog::debug("Getting widget subtree for: {} (depth: {})", widget_id, depth);

    nlohmann::json params = {
        {"objectGroup", "flutter-reflect"},
        {"arg", widget_id},
        {"subtreeDepth", std::to_string(depth)}
    };

    return callInspectorExtension("getDetailsSubtree", params);
}

WidgetTree WidgetInspector::getWidgetTree(int max_depth) {
    spdlog::info("Extracting widget tree (max_depth: {})", max_depth);

    WidgetTree tree;

    try {
        // Get root widget ID
        std::string root_id = getRootWidgetId();
        tree.setRoot(root_id);

        // Get subtree starting from root
        int depth = (max_depth > 0) ? max_depth : 100;  // Default to 100 if unlimited
        auto subtree = getWidgetSubtree(root_id, depth);

        // Extract all widget nodes from subtree
        extractWidgetNodes(subtree, tree);

        spdlog::info("Extracted widget tree: {} widgets", tree.getNodeCount());

        return tree;

    } catch (const std::exception& e) {
        spdlog::error("Failed to extract widget tree: {}", e.what());
        throw;
    }
}

void WidgetInspector::extractWidgetNodes(const nlohmann::json& subtree_data,
                                        WidgetTree& tree, const std::string& parent_id) {
    if (subtree_data.is_null()) {
        return;
    }

    // The subtree data format from Flutter inspector is complex
    // It typically contains a "result" field with diagnostic data
    nlohmann::json result;
    if (subtree_data.contains("result")) {
        result = subtree_data["result"];
    } else {
        result = subtree_data;
    }

    if (result.is_null()) {
        return;
    }

    // Parse this node
    WidgetNode node = parseWidgetNode(result, parent_id);
    tree.addNode(node);

    // Extract children recursively
    if (result.contains("children") && result["children"].is_array()) {
        for (const auto& child_data : result["children"]) {
            extractWidgetNodes(child_data, tree, node.id);
        }
    }
}

WidgetNode WidgetInspector::parseWidgetNode(const nlohmann::json& widget_data,
                                           const std::string& parent_id) {
    WidgetNode node;
    node.parent_id = parent_id;

    // Extract widget ID
    if (widget_data.contains("objectId")) {
        node.id = widget_data["objectId"].get<std::string>();
    } else if (widget_data.contains("valueId")) {
        node.id = widget_data["valueId"].get<std::string>();
    } else {
        node.id = "unknown";
    }

    // Extract widget type/class name from description
    // The "type" field is always "_ElementDiagnosticableTreeNode", so we use description
    if (widget_data.contains("description")) {
        node.description = widget_data["description"].get<std::string>();

        // Extract type from description (usually first word)
        size_t space_pos = node.description.find(' ');
        if (space_pos != std::string::npos) {
            node.type = node.description.substr(0, space_pos);
        } else {
            node.type = node.description;
        }
    } else {
        // Fallback: use "type" field if description not available
        if (widget_data.contains("type") && !widget_data["type"].is_null()) {
            node.type = widget_data["type"].get<std::string>();
        } else {
            node.type = "Unknown";
        }
    }

    // Extract children IDs
    if (widget_data.contains("children") && widget_data["children"].is_array()) {
        for (const auto& child : widget_data["children"]) {
            if (child.contains("objectId")) {
                node.children_ids.push_back(child["objectId"].get<std::string>());
            } else if (child.contains("valueId")) {
                node.children_ids.push_back(child["valueId"].get<std::string>());
            }
        }
    }

    // Extract properties
    if (widget_data.contains("properties") && widget_data["properties"].is_array()) {
        node.properties = widget_data["properties"];

        // Parse common properties
        extractTextProperty(node, widget_data["properties"]);
        extractBoundsProperty(node, widget_data["properties"]);
        extractStateProperties(node, widget_data["properties"]);
    }

    spdlog::debug("Parsed widget: {} ({})", node.type, node.id);

    return node;
}

void WidgetInspector::extractTextProperty(WidgetNode& node,
                                         const nlohmann::json& properties) {
    if (!properties.is_array()) {
        return;
    }

    // Look for "data" or "text" property in diagnostic properties
    for (const auto& prop : properties) {
        if (!prop.contains("name")) {
            continue;
        }

        std::string prop_name = prop["name"].get<std::string>();

        if (prop_name == "data" || prop_name == "text") {
            if (prop.contains("value") && prop["value"].is_string()) {
                node.text = prop["value"].get<std::string>();
                spdlog::debug("Found text property: {}", node.text.value());
                return;
            }
        }
    }
}

void WidgetInspector::extractBoundsProperty(WidgetNode& node,
                                           const nlohmann::json& properties) {
    if (!properties.is_array()) {
        return;
    }

    // Look for bounds/rect/size properties
    for (const auto& prop : properties) {
        if (!prop.contains("name")) {
            continue;
        }

        std::string prop_name = prop["name"].get<std::string>();

        if (prop_name == "renderObject" && prop.contains("properties")) {
            // Render object might have bounds
            auto render_props = prop["properties"];
            for (const auto& render_prop : render_props) {
                if (!render_prop.contains("name")) {
                    continue;
                }

                std::string render_prop_name = render_prop["name"].get<std::string>();

                if (render_prop_name == "size" && render_prop.contains("value")) {
                    // Parse size (usually "Size(width, height)")
                    std::string size_str = render_prop["value"].get<std::string>();
                    // TODO: Parse size string into width/height
                    spdlog::debug("Found size property: {}", size_str);
                }
            }
        }
    }
}

void WidgetInspector::extractStateProperties(WidgetNode& node,
                                            const nlohmann::json& properties) {
    if (!properties.is_array()) {
        return;
    }

    // Assume enabled/visible by default
    node.enabled = true;
    node.visible = true;

    for (const auto& prop : properties) {
        if (!prop.contains("name")) {
            continue;
        }

        std::string prop_name = prop["name"].get<std::string>();

        if (prop_name == "enabled" && prop.contains("value")) {
            if (prop["value"].is_boolean()) {
                node.enabled = prop["value"].get<bool>();
            }
        }

        if (prop_name == "visible" && prop.contains("value")) {
            if (prop["value"].is_boolean()) {
                node.visible = prop["value"].get<bool>();
            }
        }
    }
}

} // namespace flutter
