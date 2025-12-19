#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <optional>
#include <nlohmann/json.hpp>

namespace flutter {

/**
 * @brief Widget bounds (position and size)
 */
struct WidgetBounds {
    double x = 0.0;
    double y = 0.0;
    double width = 0.0;
    double height = 0.0;

    bool isValid() const {
        return width > 0 && height > 0;
    }

    nlohmann::json toJson() const {
        return {
            {"x", x},
            {"y", y},
            {"width", width},
            {"height", height}
        };
    }
};

/**
 * @brief Represents a single widget in the widget tree
 */
struct WidgetNode {
    std::string id;                          // Unique widget ID from inspector
    std::string type;                        // Widget class name (e.g., "Text", "ElevatedButton")
    std::string description;                 // Short description

    // Common properties
    std::optional<std::string> text;         // Text content (for Text, Button, etc.)
    std::optional<WidgetBounds> bounds;      // Position and size
    bool enabled = true;                     // Whether widget is enabled
    bool visible = true;                     // Whether widget is visible

    // Hierarchy
    std::string parent_id;                   // Parent widget ID (empty for root)
    std::vector<std::string> children_ids;   // Child widget IDs

    // Additional properties from inspector
    nlohmann::json properties;               // All diagnostic properties

    /**
     * @brief Check if widget has text content
     */
    bool hasText() const {
        return text.has_value() && !text.value().empty();
    }

    /**
     * @brief Check if widget has bounds
     */
    bool hasBounds() const {
        return bounds.has_value() && bounds.value().isValid();
    }

    /**
     * @brief Get display name for widget (type + text if available)
     */
    std::string getDisplayName() const {
        if (hasText()) {
            return type + "['" + text.value() + "']";
        }
        return type;
    }

    /**
     * @brief Convert to JSON representation
     */
    nlohmann::json toJson() const {
        nlohmann::json j = {
            {"id", id},
            {"type", type},
            {"enabled", enabled},
            {"visible", visible},
            {"children_count", children_ids.size()}
        };

        if (!description.empty()) {
            j["description"] = description;
        }

        if (hasText()) {
            j["text"] = text.value();
        }

        if (hasBounds()) {
            j["bounds"] = bounds.value().toJson();
        }

        if (!parent_id.empty()) {
            j["parent_id"] = parent_id;
        }

        if (!children_ids.empty()) {
            j["children_ids"] = children_ids;
        }

        // Include additional properties if any
        if (!properties.empty()) {
            j["properties"] = properties;
        }

        return j;
    }
};

/**
 * @brief Represents the complete widget tree
 */
class WidgetTree {
public:
    WidgetTree() = default;

    /**
     * @brief Set the root widget
     */
    void setRoot(const std::string& root_id) {
        root_id_ = root_id;
    }

    /**
     * @brief Get root widget ID
     */
    std::string getRootId() const {
        return root_id_;
    }

    /**
     * @brief Add a widget node to the tree
     */
    void addNode(const WidgetNode& node) {
        nodes_[node.id] = node;
    }

    /**
     * @brief Get a widget node by ID
     */
    std::optional<WidgetNode> getNode(const std::string& id) const {
        auto it = nodes_.find(id);
        if (it != nodes_.end()) {
            return it->second;
        }
        return std::nullopt;
    }

    /**
     * @brief Get all nodes
     */
    const std::unordered_map<std::string, WidgetNode>& getAllNodes() const {
        return nodes_;
    }

    /**
     * @brief Get total widget count
     */
    size_t getNodeCount() const {
        return nodes_.size();
    }

    /**
     * @brief Check if tree has a root
     */
    bool hasRoot() const {
        return !root_id_.empty() && nodes_.find(root_id_) != nodes_.end();
    }

    /**
     * @brief Get children of a widget
     */
    std::vector<WidgetNode> getChildren(const std::string& parent_id) const {
        std::vector<WidgetNode> children;
        auto parent = getNode(parent_id);
        if (!parent.has_value()) {
            return children;
        }

        for (const auto& child_id : parent.value().children_ids) {
            auto child = getNode(child_id);
            if (child.has_value()) {
                children.push_back(child.value());
            }
        }

        return children;
    }

    /**
     * @brief Format tree as indented text (for LLM consumption)
     * @param max_depth Maximum depth to traverse (0 = unlimited)
     */
    std::string toText(int max_depth = 0) const;

    /**
     * @brief Format tree as JSON
     */
    nlohmann::json toJson() const {
        nlohmann::json j = {
            {"root_id", root_id_},
            {"node_count", nodes_.size()},
            {"nodes", nlohmann::json::array()}
        };

        // Convert all nodes to JSON
        for (const auto& [id, node] : nodes_) {
            j["nodes"].push_back(node.toJson());
        }

        return j;
    }

    /**
     * @brief Clear the tree
     */
    void clear() {
        root_id_.clear();
        nodes_.clear();
    }

private:
    std::string root_id_;
    std::unordered_map<std::string, WidgetNode> nodes_;

    // Helper for text formatting
    void formatNodeText(std::string& output, const std::string& node_id,
                       int depth, int max_depth, const std::string& indent) const;
};

} // namespace flutter
