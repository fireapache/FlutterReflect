#pragma once

#include <string>
#include <vector>
#include <optional>
#include <memory>
#include <regex>
#include "widget_tree.h"

namespace flutter {

/**
 * @brief Selector token types for matching widgets
 */
enum class SelectorTokenType {
    Type,              // Matches widget type: "Button"
    TextEquals,        // Matches by exact text: [text="Login"]
    TextContains,      // Matches by text contains: [contains="log"]
    PropertyEquals,    // Matches by property: [enabled=true]
    DirectChild,       // Direct child selector: >
    Descendant,        // Descendant selector: (space)
    Id,                // ID selector: #widget-id
};

/**
 * @brief Single token in a selector
 */
struct SelectorToken {
    SelectorTokenType type;
    std::string value;                        // For Type, Id
    std::string attribute;                    // For Text*, Property* tokens
    std::optional<std::string> expected_value; // For equals comparisons
};

/**
 * @brief Parsed selector with multiple tokens
 *
 * Supports CSS-like syntax for finding widgets:
 * - Button                          // Match by type
 * - Text[text="Login"]              // Match by exact text
 * - TextField[contains="email"]     // Match by text contains
 * - Column > Text                   // Direct child selector
 * - Container Text                  // Descendant selector
 * - Button[enabled=true]            // Match by property
 * - #widget-id                      // Match by ID
 */
class Selector {
public:
    /**
     * @brief Parse a selector string into a Selector object
     * @param selector_str CSS-like selector string
     * @return Parsed Selector object
     * @throws std::runtime_error if selector is invalid
     */
    static Selector parse(const std::string& selector_str);

    /**
     * @brief Find all widgets matching this selector in the tree
     * @param tree Widget tree to search in
     * @return Vector of matching widgets
     */
    std::vector<WidgetNode> match(const WidgetTree& tree) const;

    /**
     * @brief Find the first widget matching this selector
     * @param tree Widget tree to search in
     * @return First matching widget, or empty optional if none found
     */
    std::optional<WidgetNode> matchFirst(const WidgetTree& tree) const;

    /**
     * @brief Get string representation of this selector
     * @return Selector string
     */
    std::string toString() const;

private:
    std::vector<SelectorToken> tokens_;

    /**
     * @brief Check if a single token matches a widget node
     * @param node Widget node to test
     * @param token Selector token to match against
     * @return True if token matches node
     */
    bool matchesToken(const WidgetNode& node, const SelectorToken& token) const;

    /**
     * @brief Get all direct children of a node from the tree
     * @param tree Widget tree
     * @param parent_id Parent widget ID
     * @return Vector of child nodes
     */
    std::vector<WidgetNode> getDirectChildren(const WidgetTree& tree,
                                               const std::string& parent_id) const;

    /**
     * @brief Get all descendants of a node (recursive)
     * @param tree Widget tree
     * @param parent_id Root widget ID
     * @param depth Current depth for logging
     * @return Vector of all descendant nodes
     */
    std::vector<WidgetNode> getDescendants(const WidgetTree& tree,
                                            const std::string& parent_id,
                                            int depth = 0) const;

    /**
     * @brief Match tokens starting from a specific root
     * @param tree Widget tree
     * @param root_id Root widget ID to start matching from
     * @param token_index Which token in tokens_ to match
     * @return Vector of matching nodes
     */
    std::vector<WidgetNode> matchTokensFrom(const WidgetTree& tree,
                                             const std::string& root_id,
                                             size_t token_index) const;

    /**
     * @brief Parse property value (handle booleans, numbers, strings)
     * @param value_str String representation of value
     * @return Parsed value
     */
    static std::string parsePropertyValue(const std::string& value_str);

    /**
     * @brief Extract widget property from diagnostic properties
     * @param node Widget node
     * @param property_name Name of property to extract
     * @return Property value, or empty string if not found
     */
    static std::string getWidgetProperty(const WidgetNode& node,
                                         const std::string& property_name);
};

} // namespace flutter
