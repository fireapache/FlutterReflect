#pragma once

#include "flutter/vm_service_client.h"
#include "flutter/widget_tree.h"
#include <memory>
#include <string>

namespace flutter {

/**
 * @brief High-level wrapper for Flutter's WidgetInspectorService
 *
 * Provides methods to query widget trees, properties, and structure
 * from a running Flutter application via the VM Service Protocol.
 */
class WidgetInspector {
public:
    /**
     * @brief Construct inspector with VM Service client
     * @param client Shared pointer to VM Service client (must be connected)
     */
    explicit WidgetInspector(std::shared_ptr<VMServiceClient> client);

    /**
     * @brief Get the complete widget tree
     * @param max_depth Maximum depth to traverse (0 = unlimited)
     * @return WidgetTree containing all extracted widgets
     * @throws std::runtime_error if not connected or extraction fails
     */
    WidgetTree getWidgetTree(int max_depth = 0);

    /**
     * @brief Get root widget ID
     * @return Root widget ID string
     * @throws std::runtime_error if inspector service not available
     */
    std::string getRootWidgetId();

    /**
     * @brief Get widget details including properties
     * @param widget_id Widget ID to query
     * @return JSON object with widget details
     * @throws std::runtime_error if widget not found
     */
    nlohmann::json getWidgetDetails(const std::string& widget_id);

    /**
     * @brief Get widget subtree starting from a widget
     * @param widget_id Widget ID to start from
     * @param depth Maximum depth to traverse
     * @return JSON object with subtree data
     * @throws std::runtime_error if widget not found
     */
    nlohmann::json getWidgetSubtree(const std::string& widget_id, int depth = 10);

private:
    std::shared_ptr<VMServiceClient> vm_client_;
    std::string isolate_id_;

    // Inspector service extension calls
    nlohmann::json callInspectorExtension(const std::string& method,
                                         const nlohmann::json& params);

    // Widget tree extraction helpers
    void extractWidgetNodes(const nlohmann::json& subtree_data, WidgetTree& tree,
                           const std::string& parent_id = "");

    WidgetNode parseWidgetNode(const nlohmann::json& widget_data,
                              const std::string& parent_id = "");

    // Property parsing helpers
    void extractTextProperty(WidgetNode& node, const nlohmann::json& properties);
    void extractBoundsProperty(WidgetNode& node, const nlohmann::json& properties);
    void extractStateProperties(WidgetNode& node, const nlohmann::json& properties);
};

} // namespace flutter
