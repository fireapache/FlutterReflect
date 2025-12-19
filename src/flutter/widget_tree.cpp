#include "flutter/widget_tree.h"
#include <sstream>

namespace flutter {

std::string WidgetTree::toText(int max_depth) const {
    if (!hasRoot()) {
        return "(empty tree)";
    }

    std::string output;
    output += "Widget Tree:\n";
    output += "============\n\n";

    // Start formatting from root
    formatNodeText(output, root_id_, 0, max_depth, "");

    output += "\n";
    output += "Total widgets: " + std::to_string(nodes_.size()) + "\n";

    return output;
}

void WidgetTree::formatNodeText(std::string& output, const std::string& node_id,
                                int depth, int max_depth, const std::string& indent) const {
    // Check depth limit
    if (max_depth > 0 && depth >= max_depth) {
        output += indent + "  ...\n";
        return;
    }

    // Get node
    auto node_opt = getNode(node_id);
    if (!node_opt.has_value()) {
        output += indent + "  (invalid node: " + node_id + ")\n";
        return;
    }

    const auto& node = node_opt.value();

    // Format node line
    std::ostringstream line;
    line << indent;

    // Add tree structure characters
    if (depth > 0) {
        line << "├─ ";
    }

    // Add widget type
    line << node.type;

    // Add text content if available
    if (node.hasText()) {
        line << " [\"" << node.text.value() << "\"]";
    }

    // Add ID for reference
    line << " (id: " << node.id.substr(node.id.find_last_of('/') + 1) << ")";

    // Add state indicators
    if (!node.enabled) {
        line << " [disabled]";
    }
    if (!node.visible) {
        line << " [hidden]";
    }

    // Add bounds if available
    if (node.hasBounds()) {
        const auto& bounds = node.bounds.value();
        line << " @(" << static_cast<int>(bounds.x) << "," << static_cast<int>(bounds.y)
             << " " << static_cast<int>(bounds.width) << "x" << static_cast<int>(bounds.height) << ")";
    }

    // Add children count
    if (!node.children_ids.empty()) {
        line << " {" << node.children_ids.size() << " children}";
    }

    line << "\n";
    output += line.str();

    // Recursively format children
    if (!node.children_ids.empty()) {
        std::string child_indent = indent;
        if (depth > 0) {
            child_indent += "│  ";
        }

        for (size_t i = 0; i < node.children_ids.size(); ++i) {
            const auto& child_id = node.children_ids[i];

            // Use different prefix for last child
            std::string child_prefix = child_indent;
            if (i == node.children_ids.size() - 1) {
                child_prefix += "└─ ";
            }

            formatNodeText(output, child_id, depth + 1, max_depth,
                          i == node.children_ids.size() - 1 ? child_indent + "   " : child_indent);
        }
    }
}

} // namespace flutter
