#include "flutter/selector.h"
#include <spdlog/spdlog.h>
#include <sstream>
#include <algorithm>
#include <cctype>

namespace flutter {

// Helper to trim whitespace from both ends
static std::string trim(const std::string& str) {
    auto start = std::find_if_not(str.begin(), str.end(), [](unsigned char c) {
        return std::isspace(c);
    });
    auto end = std::find_if_not(str.rbegin(), str.rend(), [](unsigned char c) {
        return std::isspace(c);
    }).base();
    return (start < end) ? std::string(start, end) : std::string();
}

// Helper to check if string starts with prefix
static bool startsWith(const std::string& str, const std::string& prefix) {
    return str.size() >= prefix.size() &&
           str.compare(0, prefix.size(), prefix) == 0;
}

// Helper to check if string contains substring
static bool contains(const std::string& str, const std::string& substr) {
    return str.find(substr) != std::string::npos;
}

Selector Selector::parse(const std::string& selector_str) {
    Selector selector;
    std::string input = trim(selector_str);

    if (input.empty()) {
        throw std::runtime_error("Empty selector string");
    }

    spdlog::debug("Parsing selector: {}", input);

    size_t pos = 0;
    SelectorToken current_token;
    bool expecting_token = true;

    while (pos < input.size()) {
        // Skip whitespace
        while (pos < input.size() && std::isspace(input[pos])) {
            // Check if we need to insert a descendant selector
            if (!selector.tokens_.empty() && expecting_token) {
                SelectorToken descendant_token;
                descendant_token.type = SelectorTokenType::Descendant;
                selector.tokens_.push_back(descendant_token);
                expecting_token = false;
            }
            pos++;
        }

        if (pos >= input.size()) break;

        // Check for direct child selector '>'
        if (input[pos] == '>') {
            if (selector.tokens_.empty()) {
                throw std::runtime_error("Selector cannot start with '>'");
            }
            SelectorToken token;
            token.type = SelectorTokenType::DirectChild;
            selector.tokens_.push_back(token);
            pos++;
            expecting_token = true;
            continue;
        }

        // Check for ID selector '#'
        if (input[pos] == '#') {
            pos++;
            size_t id_start = pos;
            while (pos < input.size() &&
                   (std::isalnum(input[pos]) || input[pos] == '_' || input[pos] == '-')) {
                pos++;
            }

            if (pos == id_start) {
                throw std::runtime_error("Empty ID selector");
            }

            SelectorToken token;
            token.type = SelectorTokenType::Id;
            token.value = input.substr(id_start, pos - id_start);
            selector.tokens_.push_back(token);
            expecting_token = false;
            continue;
        }

        // Parse type selector and attributes
        size_t type_start = pos;
        while (pos < input.size() &&
               (std::isalnum(input[pos]) || input[pos] == '_')) {
            pos++;
        }

        if (pos > type_start) {
            // We have a type selector
            SelectorToken token;
            token.type = SelectorTokenType::Type;
            token.value = input.substr(type_start, pos - type_start);
            selector.tokens_.push_back(token);
            expecting_token = false;
        }

        // Check for attribute selector '['
        while (pos < input.size() && input[pos] == '[') {
            pos++; // Skip '['

            // Skip whitespace
            while (pos < input.size() && std::isspace(input[pos])) pos++;

            // Parse attribute name
            size_t attr_start = pos;
            while (pos < input.size() &&
                   (std::isalnum(input[pos]) || input[pos] == '_')) {
                pos++;
            }

            if (pos == attr_start) {
                throw std::runtime_error("Empty attribute name in selector");
            }

            std::string attr_name = input.substr(attr_start, pos - attr_start);

            // Skip whitespace
            while (pos < input.size() && std::isspace(input[pos])) pos++;

            SelectorToken attr_token;

            // Check for comparison operator
            if (pos < input.size() && input[pos] == '=') {
                pos++; // Skip '='

                // Skip whitespace
                while (pos < input.size() && std::isspace(input[pos])) pos++;

                // Parse value (can be quoted or unquoted)
                std::string value;
                if (pos < input.size() && (input[pos] == '"' || input[pos] == '\'')) {
                    char quote = input[pos];
                    pos++; // Skip opening quote
                    size_t value_start = pos;
                    while (pos < input.size() && input[pos] != quote) {
                        pos++;
                    }
                    if (pos >= input.size()) {
                        throw std::runtime_error("Unterminated string in selector");
                    }
                    value = input.substr(value_start, pos - value_start);
                    pos++; // Skip closing quote
                } else {
                    // Unquoted value (until whitespace or ']')
                    size_t value_start = pos;
                    while (pos < input.size() &&
                           !std::isspace(input[pos]) && input[pos] != ']') {
                        pos++;
                    }
                    value = input.substr(value_start, pos - value_start);
                }

                // Determine token type based on attribute name
                if (attr_name == "text") {
                    attr_token.type = SelectorTokenType::TextEquals;
                    attr_token.expected_value = value;
                } else if (attr_name == "contains") {
                    attr_token.type = SelectorTokenType::TextContains;
                    attr_token.expected_value = value;
                } else {
                    attr_token.type = SelectorTokenType::PropertyEquals;
                    attr_token.attribute = attr_name;
                    attr_token.expected_value = value;
                }
            } else {
                // No '=' means just check property exists
                // For backwards compatibility, treat as property equals check
                throw std::runtime_error("Attribute selector must have '=' operator: [" + attr_name + "=value]");
            }

            selector.tokens_.push_back(attr_token);

            // Skip whitespace
            while (pos < input.size() && std::isspace(input[pos])) pos++;

            // Expect ']'
            if (pos >= input.size() || input[pos] != ']') {
                throw std::runtime_error("Expected ']' to close attribute selector");
            }
            pos++; // Skip ']'
        }
    }

    if (selector.tokens_.empty()) {
        throw std::runtime_error("No valid tokens in selector");
    }

    spdlog::debug("Parsed selector into {} tokens", selector.tokens_.size());
    return selector;
}

std::vector<WidgetNode> Selector::match(const WidgetTree& tree) const {
    if (tokens_.empty()) {
        return {};
    }

    if (!tree.hasRoot()) {
        spdlog::warn("Widget tree has no root");
        return {};
    }

    // Start matching from root
    return matchTokensFrom(tree, tree.getRootId(), 0);
}

std::optional<WidgetNode> Selector::matchFirst(const WidgetTree& tree) const {
    auto matches = match(tree);
    if (!matches.empty()) {
        return matches[0];
    }
    return std::nullopt;
}

std::string Selector::toString() const {
    std::stringstream ss;
    for (size_t i = 0; i < tokens_.size(); i++) {
        const auto& token = tokens_[i];

        if (i > 0) {
            ss << " ";
        }

        switch (token.type) {
            case SelectorTokenType::Type:
                ss << token.value;
                break;
            case SelectorTokenType::Id:
                ss << "#" << token.value;
                break;
            case SelectorTokenType::TextEquals:
                ss << "[text=\"" << token.expected_value.value_or("") << "\"]";
                break;
            case SelectorTokenType::TextContains:
                ss << "[contains=\"" << token.expected_value.value_or("") << "\"]";
                break;
            case SelectorTokenType::PropertyEquals:
                ss << "[" << token.attribute << "=\""
                   << token.expected_value.value_or("") << "\"]";
                break;
            case SelectorTokenType::DirectChild:
                ss << ">";
                break;
            case SelectorTokenType::Descendant:
                ss << "(descendant)";
                break;
        }
    }
    return ss.str();
}

bool Selector::matchesToken(const WidgetNode& node, const SelectorToken& token) const {
    switch (token.type) {
        case SelectorTokenType::Type:
            return node.type == token.value;

        case SelectorTokenType::Id:
            return node.id == token.value;

        case SelectorTokenType::TextEquals:
            if (!token.expected_value.has_value()) return false;
            return node.hasText() && node.text.value() == token.expected_value.value();

        case SelectorTokenType::TextContains:
            if (!token.expected_value.has_value()) return false;
            return node.hasText() && contains(node.text.value(), token.expected_value.value());

        case SelectorTokenType::PropertyEquals: {
            if (!token.expected_value.has_value()) return false;
            std::string prop_value = getWidgetProperty(node, token.attribute);
            std::string expected = parsePropertyValue(token.expected_value.value());
            return prop_value == expected;
        }

        case SelectorTokenType::DirectChild:
        case SelectorTokenType::Descendant:
            // These are handled by matchTokensFrom, not by individual matching
            return true;
    }

    return false;
}

std::vector<WidgetNode> Selector::getDirectChildren(const WidgetTree& tree,
                                                     const std::string& parent_id) const {
    return tree.getChildren(parent_id);
}

std::vector<WidgetNode> Selector::getDescendants(const WidgetTree& tree,
                                                   const std::string& parent_id,
                                                   int depth) const {
    std::vector<WidgetNode> descendants;
    auto children = tree.getChildren(parent_id);

    for (const auto& child : children) {
        descendants.push_back(child);
        // Recursively get descendants
        auto child_descendants = getDescendants(tree, child.id, depth + 1);
        descendants.insert(descendants.end(), child_descendants.begin(), child_descendants.end());
    }

    return descendants;
}

std::vector<WidgetNode> Selector::matchTokensFrom(const WidgetTree& tree,
                                                    const std::string& root_id,
                                                    size_t token_index) const {
    std::vector<WidgetNode> results;

    if (token_index >= tokens_.size()) {
        // All tokens matched, return the root node
        auto node = tree.getNode(root_id);
        if (node.has_value()) {
            results.push_back(node.value());
        }
        return results;
    }

    const auto& token = tokens_[token_index];

    // Handle relationship tokens (DirectChild, Descendant)
    if (token.type == SelectorTokenType::DirectChild) {
        // Next token should match direct children
        auto children = getDirectChildren(tree, root_id);
        for (const auto& child : children) {
            auto child_matches = matchTokensFrom(tree, child.id, token_index + 1);
            results.insert(results.end(), child_matches.begin(), child_matches.end());
        }
        return results;
    }

    if (token.type == SelectorTokenType::Descendant) {
        // Next token should match any descendant
        auto descendants = getDescendants(tree, root_id);
        for (const auto& descendant : descendants) {
            auto desc_matches = matchTokensFrom(tree, descendant.id, token_index + 1);
            results.insert(results.end(), desc_matches.begin(), desc_matches.end());
        }
        return results;
    }

    // For the first token, we need to check if root matches
    auto root_node = tree.getNode(root_id);
    if (!root_node.has_value()) {
        return results;
    }

    // Check if current node matches the token
    if (matchesToken(root_node.value(), token)) {
        // Check if this is the last token
        if (token_index == tokens_.size() - 1) {
            results.push_back(root_node.value());
        } else {
            // Look ahead to see if next token is a relationship token
            if (token_index + 1 < tokens_.size()) {
                const auto& next_token = tokens_[token_index + 1];
                if (next_token.type == SelectorTokenType::DirectChild ||
                    next_token.type == SelectorTokenType::Descendant) {
                    // Continue matching from this node
                    auto child_matches = matchTokensFrom(tree, root_id, token_index + 1);
                    results.insert(results.end(), child_matches.begin(), child_matches.end());
                }
            }
        }
    }

    // Also search descendants if we haven't matched everything yet
    if (token_index == 0) {
        auto descendants = getDescendants(tree, root_id);
        for (const auto& descendant : descendants) {
            auto desc_matches = matchTokensFrom(tree, descendant.id, token_index);
            results.insert(results.end(), desc_matches.begin(), desc_matches.end());
        }
    }

    return results;
}

std::string Selector::parsePropertyValue(const std::string& value_str) {
    std::string trimmed = trim(value_str);

    // Convert "true"/"false" to lowercase
    if (trimmed == "true" || trimmed == "True" || trimmed == "TRUE") {
        return "true";
    }
    if (trimmed == "false" || trimmed == "False" || trimmed == "FALSE") {
        return "false";
    }

    return trimmed;
}

std::string Selector::getWidgetProperty(const WidgetNode& node,
                                        const std::string& property_name) {
    // Check special properties first
    if (property_name == "enabled") {
        return node.enabled ? "true" : "false";
    }
    if (property_name == "visible") {
        return node.visible ? "true" : "false";
    }
    if (property_name == "text" && node.hasText()) {
        return node.text.value();
    }
    if (property_name == "type") {
        return node.type;
    }

    // Check in properties JSON
    if (node.properties.contains(property_name)) {
        const auto& prop = node.properties[property_name];
        if (prop.is_string()) {
            return prop.get<std::string>();
        } else if (prop.is_boolean()) {
            return prop.get<bool>() ? "true" : "false";
        } else if (prop.is_number()) {
            return std::to_string(prop.get<double>());
        }
    }

    return "";
}

} // namespace flutter
