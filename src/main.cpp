#include "mcp/server.h"
#include "mcp/transport.h"
#include "mcp/types.h"
#include "tools/connect_tool.cpp"  // Include tool implementations
#include "tools/get_tree_tool.cpp"
#include "tools/find_tool.cpp"
#include "tools/tap_tool.cpp"
#include "tools/type_tool.cpp"
#include "tools/scroll_tool.cpp"
#include "tools/get_properties_tool.cpp"
#include "tools/list_instances_tool.cpp"
#include "tools/launch_tool.cpp"
#include <spdlog/spdlog.h>
#include <spdlog/sinks/stdout_color_sinks.h>
#include <spdlog/sinks/basic_file_sink.h>
#include <iostream>
#include <csignal>
#include <atomic>
#include <algorithm>

#ifdef _WIN32
#include <windows.h>
#endif

std::atomic<bool> shutdown_requested(false);
mcp::Server* global_server = nullptr;

void signal_handler(int signal) {
    spdlog::info("Received signal {}, shutting down", signal);
    shutdown_requested = true;
    if (global_server) {
        global_server->stop();
    }
}

void setup_signal_handlers() {
    std::signal(SIGINT, signal_handler);
    std::signal(SIGTERM, signal_handler);
#ifndef _WIN32
    std::signal(SIGPIPE, SIG_IGN);  // Ignore broken pipe on Unix
#endif
}

// Extract just the executable name from the full path and remove .exe suffix
static std::string get_program_name(const char* full_path) {
    std::string path(full_path);

    // Remove path, keeping only filename
    size_t last_slash = path.find_last_of("/\\");
    if (last_slash != std::string::npos) {
        path = path.substr(last_slash + 1);
    }

    // Remove .exe suffix if present
    if (path.length() >= 4 && path.substr(path.length() - 4) == ".exe") {
        path = path.substr(0, path.length() - 4);
    }

    return path;
}

void print_usage(const char* program_name) {
    std::string short_name = get_program_name(program_name);
    std::cerr << "+------------------------------------------------------------------------------+\n"
              << "|              FlutterReflect - Flutter UI Automation MCP                  |\n"
              << "|                                                                              |\n"
              << "|  Enables AI agents to autonomously discover, launch, and interact with      |\n"
              << "|  Flutter applications without manual intervention.                          |\n"
              << "+------------------------------------------------------------------------------+\n\n"
              << "USAGE:\n"
              << "  MCP Server Mode:  " << short_name << " [OPTIONS]\n"
              << "  CLI Tool Mode:    " << short_name << " <tool_name> [TOOL_OPTIONS]\n\n"
              << "===============================================================================\n"
              << "OPTIONS:\n"
              << "===============================================================================\n"
              << "  -h, --help              Display this help message and exit\n"
              << "  -v, --version           Display version information and exit\n"
              << "  --log-level LEVEL       Set logging level: debug, info, warn, error\n"
              << "                          [default: info]\n"
              << "  --log-file PATH         Log to file instead of stderr\n\n"
              << "===============================================================================\n"
              << "AVAILABLE TOOLS:\n"
              << "===============================================================================\n\n"
              << "  list_instances:\n"
              << "    Auto-discover running Flutter applications on your system by scanning\n"
              << "    a configurable port range. Returns comprehensive metadata including VM\n"
              << "    Service URIs, ports, project names, device types, and connection status.\n"
              << "    Enables zero-configuration autonomous discovery without manual setup.\n"
              << "    \n"
              << "    Use Case: Initial discovery before connecting to Flutter apps\n"
              << "    Parameters:\n"
              << "      --port-start <int>    Start of port range (default: 8080)\n"
              << "      --port-end <int>      End of port range (default: 8200)\n"
              << "      --timeout-ms <int>    Timeout per port in ms (default: 500)\n"
              << "    \n"
              << "    Example: list_instances --port-start 8080 --port-end 8200\n"
              << "  ---\n\n"
              << "  launch:\n"
              << "    Launch a Flutter application programmatically and monitor its startup\n"
              << "    process. Executes 'flutter run', captures VM Service URI, monitors\n"
              << "    compilation progress, and returns when app is ready for interaction.\n"
              << "    Supports custom device selection and VM Service port configuration.\n"
              << "    \n"
              << "    Use Case: Start Flutter apps for automated testing or development\n"
              << "    Parameters:\n"
              << "      --project-path <path>     Path to Flutter project (required)\n"
              << "      --device <id>             Target device ID (default: auto)\n"
              << "      --vm-service-port <int>   VM Service port (default: auto)\n"
              << "      --disable-auth <bool>     Disable auth code (default: false)\n"
              << "      --startup-timeout <int>   Startup timeout in seconds (default: 60)\n"
              << "    \n"
              << "    Example: launch --project-path ./my_app\n"
              << "  ---\n\n"
              << "  connect:\n"
              << "    Establish WebSocket connection to Flutter app's VM Service for remote\n"
              << "    debugging and interaction. Supports both manual URI specification and\n"
              << "    autonomous auto-discovery mode. When URI is omitted, automatically\n"
              << "    discovers and connects to the first available Flutter instance. Handles\n"
              << "    authentication, protocol negotiation, and connection state management.\n"
              << "    \n"
              << "    Use Case: Connect to Flutter app before inspection or interaction\n"
              << "    Parameters:\n"
              << "      --uri <ws://...>          VM Service WebSocket URI (optional)\n"
              << "      --auth-token <token>      Authentication token (if required)\n"
              << "      --port <int>              Port number for auto-discovery\n"
              << "      --project-name <name>     Project name filter for auto-discovery\n"
              << "      --instance-index <int>    Instance index when multiple apps running\n"
              << "    \n"
              << "    Example: connect --uri ws://localhost:8181/abc\n"
              << "    Example: connect  # Auto-discovers first instance\n"
              << "  ---\n\n"
              << "  disconnect:\n"
              << "    Gracefully disconnect from the currently active Flutter application.\n"
              << "    Closes WebSocket connection, releases VM Service resources, and cleans\n"
              << "    up internal connection state. Safe to call multiple times.\n"
              << "    \n"
              << "    Use Case: Clean disconnection after interaction or before switching apps\n"
              << "    Parameters: (none)\n"
              << "    \n"
              << "    Example: disconnect\n"
              << "  ---\n\n"
              << "  get_tree:\n"
              << "    Retrieve the complete widget tree hierarchy from the connected Flutter\n"
              << "    application. Returns structured representation of all widgets including\n"
              << "    types, IDs, text content, bounds, and parent-child relationships.\n"
              << "    Supports configurable depth limits and output formats (text/JSON).\n"
              << "    Essential for understanding app structure and locating UI elements.\n"
              << "    \n"
              << "    Use Case: Inspect app structure, locate widgets, verify UI hierarchy\n"
              << "    Parameters:\n"
              << "      --max-depth <int>         Maximum tree depth (default: unlimited)\n"
              << "      --format <text|json>      Output format (default: text)\n"
              << "    \n"
              << "    Example: get_tree --max-depth 5 --format json\n"
              << "  ---\n\n"
              << "  get_properties:\n"
              << "    Extract detailed properties and diagnostic information from specific\n"
              << "    widgets. Returns comprehensive data including geometric bounds, enabled\n"
              << "    state, render object details, layout constraints, and custom properties.\n"
              << "    Supports both widget ID and CSS selector-based targeting.\n"
              << "    \n"
              << "    Use Case: Deep inspection of widget state and properties\n"
              << "    Parameters:\n"
              << "      --widget-id <id>          Target widget by ID\n"
              << "      --selector <css>          Target widget by CSS selector\n"
              << "      --include-render <bool>   Include render object info (default: false)\n"
              << "      --include-layout <bool>   Include layout details (default: false)\n"
              << "      --include-children <bool> Include child widgets (default: false)\n"
              << "      --max-depth <int>         Max child depth if included (default: 1)\n"
              << "    \n"
              << "    Example: get_properties --selector \"Button[text='Login']\"\n"
              << "  ---\n\n"
              << "  find:\n"
              << "    Locate widgets using powerful CSS-like selector syntax. Supports type\n"
              << "    matching (Button, TextField), text matching (exact and contains), property\n"
              << "    matching, and hierarchical selectors. Returns widget IDs and metadata for\n"
              << "    matched elements. Enables precise widget targeting without manual ID lookup.\n"
              << "    \n"
              << "    Use Case: Locate specific widgets for interaction or inspection\n"
              << "    Selector Syntax:\n"
              << "      Type:       Button, TextField, Text, etc.\n"
              << "      Text:       [text='Login'], [contains='Email']\n"
              << "      Property:   [enabled=true], [visible=true]\n"
              << "      Hierarchy:  Column > Button (direct child)\n"
              << "    \n"
              << "    Parameters:\n"
              << "      --selector <css>          CSS-like selector (required)\n"
              << "      --find-all <bool>         Find all matches vs first (default: false)\n"
              << "      --include-properties <bool> Include full properties (default: false)\n"
              << "    \n"
              << "    Example: find --selector \"Button[text='Login']\"\n"
              << "    Example: find --selector \"TextField[contains='email']\" --find-all true\n"
              << "  ---\n\n"
              << "  tap:\n"
              << "    Simulate user tap/click interaction on widgets or screen coordinates.\n"
              << "    Supports three targeting modes: CSS selector, widget ID, or absolute\n"
              << "    coordinates. Optionally specify offset from widget center for precise\n"
              << "    positioning. Triggers actual Flutter tap events including gesture detection.\n"
              << "    \n"
              << "    Use Case: Simulate button clicks, navigation, and user interactions\n"
              << "    Parameters:\n"
              << "      --selector <css>          Target by CSS selector\n"
              << "      --widget-id <id>          Target by widget ID\n"
              << "      --x <double>              X coordinate (for coordinate mode)\n"
              << "      --y <double>              Y coordinate (for coordinate mode)\n"
              << "      --x-offset <double>       X offset from widget center (default: 0)\n"
              << "      --y-offset <double>       Y offset from widget center (default: 0)\n"
              << "    \n"
              << "    Example: tap --selector \"Button[text='Login']\"\n"
              << "    Example: tap --widget-id \"button_123\"\n"
              << "    Example: tap --x 100 --y 200\n"
              << "  ---\n\n"
              << "  type:\n"
              << "    Enter text into input fields, simulating keyboard input. Automatically\n"
              << "    focuses on target widget (via selector or ID), optionally clears existing\n"
              << "    text, types the specified text, and optionally submits (presses Enter).\n"
              << "    Works with TextField, TextFormField, and other editable widgets.\n"
              << "    \n"
              << "    Use Case: Form filling, search queries, text input automation\n"
              << "    Parameters:\n"
              << "      --text <string>           Text to type (required)\n"
              << "      --selector <css>          Target by CSS selector\n"
              << "      --widget-id <id>          Target by widget ID\n"
              << "      --clear-first <bool>      Clear existing text first (default: false)\n"
              << "      --submit <bool>           Press Enter after typing (default: false)\n"
              << "    \n"
              << "    Example: type --text \"test@example.com\" --selector \"TextField\"\n"
              << "    Example: type --text \"password123\" --clear-first true --submit true\n"
              << "  ---\n\n"
              << "  scroll:\n"
              << "    Perform scroll gestures within the application or specific scrollable\n"
              << "    widgets. Supports both horizontal (dx) and vertical (dy) scrolling with\n"
              << "    configurable animation duration and velocity. Can target specific widgets\n"
              << "    or scroll the entire view.\n"
              << "    \n"
              << "    Use Case: Navigate long lists, access off-screen content, scroll testing\n"
              << "    Parameters:\n"
              << "      --selector <css>          Target scrollable widget (optional)\n"
              << "      --dx <double>             Horizontal scroll offset (default: 0)\n"
              << "      --dy <double>             Vertical scroll offset (default: 0)\n"
              << "      --duration <int>          Animation duration in ms (default: 300)\n"
              << "      --frequency <int>         Scroll frequency in Hz (default: 60)\n"
              << "    \n"
              << "    Example: scroll --dy -200  # Scroll up\n"
              << "    Example: scroll --selector \"ListView\" --dy 500 --duration 500\n"
              << "  ---\n\n"
              << "===============================================================================\n"
              << "QUICK START - MCP SERVER MODE:\n"
              << "===============================================================================\n\n"
              << "1. Start the MCP server:\n"
              << "   " << short_name << "\n\n"
              << "2. Configure as MCP server in Claude Code:\n"
              << "   Add FlutterReflect to your MCP server configuration.\n"
              << "   Claude Code will automatically discover and use the available tools.\n\n"
              << "3. Use autonomous discovery in Claude Code:\n"
              << "   You: \"List all running Flutter apps\"\n"
              << "   You: \"Connect to the first Flutter app and show me the widget tree\"\n"
              << "   You: \"Tap on the Login button in my Flutter app\"\n\n"
              << "   Claude Code will autonomously use these tools:\n"
              << "   - list_instances() -> Check for running apps\n"
              << "   - connect() -> Auto-discover and connect\n"
              << "   - get_tree() -> Inspect widget hierarchy\n"
              << "   - find(selector=\"Button[text='Login']\") -> Find widgets\n"
              << "   - tap(selector=\"...\") -> Interact with app\n\n"
              << "===============================================================================\n"
              << "QUICK START - CLI TOOL MODE:\n"
              << "===============================================================================\n\n"
              << "Invoke tools directly from command line for scripting and testing:\n\n"
              << "  # Discover running Flutter apps\n"
              << "  " << short_name << " list_instances --port-start 8080 --port-end 8200\n\n"
              << "  # Connect to a specific app\n"
              << "  " << short_name << " connect --uri ws://localhost:8181/abc\n\n"
              << "  # Auto-connect to first discovered instance\n"
              << "  " << short_name << " connect\n\n"
              << "  # Get widget tree\n"
              << "  " << short_name << " get_tree --max-depth 5 --format json\n\n"
              << "  # Find widgets\n"
              << "  " << short_name << " find --selector \"Button[text='Login']\"\n\n"
              << "  # Tap on widget\n"
              << "  " << short_name << " tap --selector \"Button[text='Login']\"\n\n"
              << "  # Type text\n"
              << "  " << short_name << " type --text \"test@example.com\" --selector \"TextField\"\n\n"
              << "CLI mode returns JSON results to stdout, suitable for scripting and automation.\n\n"
              << "===============================================================================\n"
              << "LOGGING:\n"
              << "===============================================================================\n\n"
              << "Enable debug logging to troubleshoot issues:\n"
              << "  " << short_name << " --log-level debug\n\n"
              << "Log to file instead of console:\n"
              << "  " << short_name << " --log-file flutter_reflect.log\n\n"
              << "===============================================================================\n"
              << "DOCUMENTATION:\n"
              << "===============================================================================\n\n"
              << "For detailed documentation and examples, see:\n"
              << "  - AUTONOMOUS_WORKFLOW.md -> Complete autonomous workflow examples\n"
              << "  - PHASE_1_2_3_COMPLETE.md -> Implementation details\n"
              << "  - IMPLEMENTATION_COMPLETE.md -> Full feature documentation\n\n"
              << "The server communicates via STDIO using JSON-RPC 2.0 protocol.\n"
              << "It is designed to be used as an MCP server with Claude Code CLI.\n\n";
}

void print_version() {
    std::cout << "+------------------------------------------------------------------------------+\n"
              << "|                     FlutterReflect - Version Info                        |\n"
              << "+------------------------------------------------------------------------------+\n\n"
              << "Product Name:              FlutterReflect MCP Server\n"
              << "Version:                   1.0.0 (Production Ready)\n"
              << "Release Date:              December 17, 2025\n"
              << "MCP Protocol Version:      " << mcp::MCP_VERSION << "\n\n"
              << "Platform Information:\n"
              << "  Operating System:        Windows / macOS / Linux\n"
              << "  Flutter Support:         Desktop (Windows/macOS/Linux) + Web (Chrome/Edge)\n"
              << "  Compiler:                MSVC (Visual Studio 2022) / GCC / Clang\n"
              << "  C++ Standard:            C++17\n\n"
              << "Features:\n"
              << "  * Auto-Discovery        Find running Flutter apps automatically\n"
              << "  * App Launching         Start Flutter apps programmatically\n"
              << "  * VM Connection         Connect to Flutter VM Service (manual/auto)\n"
              << "  * Widget Inspection     Retrieve and analyze widget trees\n"
              << "  * Widget Selection      Find widgets using CSS-like selectors\n"
              << "  * User Interaction      Tap, type, scroll, and more\n"
              << "  * Property Inspection   Get detailed widget properties\n\n"
              << "Build Information:\n"
              << "  Tools Registered:        10 MCP tools\n"
              << "  Implementation Phases:   3 (Discovery, Launching, Connection)\n"
              << "  Modes of Operation:      Autonomous + Manual\n"
              << "  Error Handling:          Comprehensive with recovery strategies\n\n"
              << "For more information:\n"
              << "  Help:                    flutter_reflect --help\n"
              << "  Documentation:           See AUTONOMOUS_WORKFLOW.md\n"
              << "  Issues & Support:        GitHub repository\n\n";
}

spdlog::level::level_enum parse_log_level(const std::string& level) {
    if (level == "debug") return spdlog::level::debug;
    if (level == "info") return spdlog::level::info;
    if (level == "warn" || level == "warning") return spdlog::level::warn;
    if (level == "error") return spdlog::level::err;
    return spdlog::level::info;
}

// Parse CLI arguments into JSON format for tool execution
nlohmann::json parse_cli_arguments(int argc, char* argv[], int start_index) {
    nlohmann::json args;

    for (int i = start_index; i < argc; ++i) {
        std::string arg = argv[i];

        // Check if it's a flag
        if (arg.size() > 2 && arg[0] == '-' && arg[1] == '-') {
            std::string key = arg.substr(2);  // Remove "--"

            // Replace hyphens with underscores for parameter names
            std::replace(key.begin(), key.end(), '-', '_');

            // Check if next argument is the value
            if (i + 1 < argc && argv[i + 1][0] != '-') {
                std::string value = argv[++i];

                // Try to parse as number or boolean
                if (value == "true") {
                    args[key] = true;
                } else if (value == "false") {
                    args[key] = false;
                } else {
                    // Try to parse as integer
                    try {
                        size_t pos;
                        int int_val = std::stoi(value, &pos);
                        if (pos == value.length()) {
                            args[key] = int_val;
                            continue;
                        }
                    } catch (...) {}

                    // Try to parse as double
                    try {
                        size_t pos;
                        double double_val = std::stod(value, &pos);
                        if (pos == value.length()) {
                            args[key] = double_val;
                            continue;
                        }
                    } catch (...) {}

                    // Default to string
                    args[key] = value;
                }
            } else {
                // Boolean flag without value
                args[key] = true;
            }
        }
    }

    return args;
}

// Create and return all available tools
std::vector<std::unique_ptr<mcp::Tool>> create_all_tools() {
    std::vector<std::unique_ptr<mcp::Tool>> tools;

    // Phase 1: Instance discovery and launching
    tools.push_back(std::make_unique<flutter::tools::ListInstancesTool>());
    tools.push_back(std::make_unique<flutter::tools::LaunchTool>());

    // Phase 2: Connection tools
    tools.push_back(std::make_unique<flutter::tools::ConnectTool>());
    tools.push_back(std::make_unique<flutter::tools::DisconnectTool>());

    // Phase 3: Widget inspection
    tools.push_back(std::make_unique<flutter::tools::GetTreeTool>());

    // Phase 4: Widget finding
    tools.push_back(std::make_unique<flutter::tools::FindTool>());

    // Phase 5: User interaction
    tools.push_back(std::make_unique<flutter::tools::TapTool>());
    tools.push_back(std::make_unique<flutter::tools::TypeTool>());
    tools.push_back(std::make_unique<flutter::tools::ScrollTool>());

    // Phase 6: Property inspection
    tools.push_back(std::make_unique<flutter::tools::GetPropertiesTool>());

    return tools;
}

// Forward declarations for cleanup
namespace flutter::tools {
    std::shared_ptr<VMServiceClient> getVMServiceClient();
    bool isConnected();
}

// Cleanup VM connection before exit (prevents seg fault on exit)
void cleanup_vm_connection() {
    auto client = flutter::tools::getVMServiceClient();
    if (client && client->isConnected()) {
        try {
            client->disconnect();
        } catch (...) {
            // Ignore errors during cleanup
        }
    }
}

// Execute a tool directly from CLI
int execute_tool_cli(const std::string& tool_name, const nlohmann::json& arguments) {
    int exit_code = 0;

    try {
        // Create all tools
        auto tools = create_all_tools();

        // Find the requested tool
        mcp::Tool* target_tool = nullptr;
        for (const auto& tool : tools) {
            if (tool->name() == tool_name) {
                target_tool = tool.get();
                break;
            }
        }

        if (!target_tool) {
            nlohmann::json error_response = {
                {"success", false},
                {"error", "Unknown tool: " + tool_name},
                {"available_tools", nlohmann::json::array()}
            };

            for (const auto& tool : tools) {
                error_response["available_tools"].push_back(tool->name());
            }

            std::cout << error_response.dump(2) << std::endl;
            cleanup_vm_connection();
            return 1;
        }

        // Execute the tool
        nlohmann::json result = target_tool->execute(arguments);

        // Output result as JSON
        std::cout << result.dump(2) << std::endl;

        // Set exit code based on success
        exit_code = result.value("success", false) ? 0 : 1;

    } catch (const std::exception& e) {
        nlohmann::json error_response = {
            {"success", false},
            {"error", std::string("Exception: ") + e.what()}
        };
        std::cout << error_response.dump(2) << std::endl;
        exit_code = 1;
    }

    // Clean up VM connection before exit to prevent seg fault
    cleanup_vm_connection();

    return exit_code;
}

int main(int argc, char* argv[]) {
    // Check for help/version flags first
    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];
        if (arg == "--help" || arg == "-h") {
            print_usage(argv[0]);
            return 0;
        }
        else if (arg == "--version" || arg == "-v") {
            print_version();
            return 0;
        }
    }

    // Check if first argument is a tool name (CLI mode)
    if (argc > 1 && argv[1][0] != '-') {
        std::string potential_tool = argv[1];

        // List of valid tool names
        const std::vector<std::string> valid_tools = {
            "list_instances",
            "launch",
            "connect",
            "disconnect",
            "get_tree",
            "get_properties",
            "find",
            "tap",
            "type",
            "scroll"
        };

        // Check if it's a valid tool name
        bool is_tool = std::find(valid_tools.begin(), valid_tools.end(), potential_tool) != valid_tools.end();

        if (is_tool) {
            // CLI mode: Execute tool directly
            nlohmann::json arguments = parse_cli_arguments(argc, argv, 2);
            return execute_tool_cli(potential_tool, arguments);
        }
    }

    // MCP Server mode: Parse server options
    std::string log_level = "info";
    std::string log_file;

    for (int i = 1; i < argc; ++i) {
        std::string arg = argv[i];

        if (arg == "--log-level" && i + 1 < argc) {
            log_level = argv[++i];
        }
        else if (arg == "--log-file" && i + 1 < argc) {
            log_file = argv[++i];
        }
        else {
            std::cerr << "Unknown option: " << arg << "\n";
            print_usage(argv[0]);
            return 1;
        }
    }

    // Setup logging
    try {
        std::vector<spdlog::sink_ptr> sinks;

        if (!log_file.empty()) {
            // Log to file
            auto file_sink = std::make_shared<spdlog::sinks::basic_file_sink_mt>(log_file, true);
            sinks.push_back(file_sink);
        } else {
            // Log to stderr (not stdout, which is used for MCP communication)
            auto console_sink = std::make_shared<spdlog::sinks::stderr_color_sink_mt>();
            sinks.push_back(console_sink);
        }

        auto logger = std::make_shared<spdlog::logger>("flutter_reflect", sinks.begin(), sinks.end());
        logger->set_level(parse_log_level(log_level));
        logger->set_pattern("[%Y-%m-%d %H:%M:%S.%e] [%^%l%$] %v");
        spdlog::set_default_logger(logger);

        spdlog::info("FlutterReflect MCP Server v1.0.0 starting");
        spdlog::info("Log level: {}", log_level);

    } catch (const std::exception& e) {
        std::cerr << "Failed to setup logging: " << e.what() << "\n";
        return 1;
    }

    // Setup signal handlers
    setup_signal_handlers();

    try {
        // Create STDIO transport
        auto transport = std::make_unique<mcp::StdioTransport>();

        // Create server info
        mcp::ServerInfo server_info;
        server_info.name = "FlutterReflect";
        server_info.version = "1.0.0";

        // Create MCP server
        mcp::Server server(std::move(transport), server_info);
        global_server = &server;

        // Register Flutter tools (Phases 1-6)
        spdlog::info("Registering Flutter tools...");

        // Phase 1: Instance discovery and launching tools
        server.registerTool(std::make_unique<flutter::tools::ListInstancesTool>());
        server.registerTool(std::make_unique<flutter::tools::LaunchTool>());

        // Phase 2: Connection tools
        server.registerTool(std::make_unique<flutter::tools::ConnectTool>());
        server.registerTool(std::make_unique<flutter::tools::DisconnectTool>());

        // Phase 3: Widget inspection tools
        server.registerTool(std::make_unique<flutter::tools::GetTreeTool>());

        // Phase 4: Selector-based widget finding
        server.registerTool(std::make_unique<flutter::tools::FindTool>());

        // Phase 5: Widget interaction tools
        server.registerTool(std::make_unique<flutter::tools::TapTool>());
        server.registerTool(std::make_unique<flutter::tools::TypeTool>());
        server.registerTool(std::make_unique<flutter::tools::ScrollTool>());

        // Phase 6: Property inspection
        server.registerTool(std::make_unique<flutter::tools::GetPropertiesTool>());

        int tool_count = static_cast<int>(server.getTools().size());
        spdlog::info("Registered {} Flutter tools", tool_count);

        // Start server
        server.start();

        // Server stopped
        spdlog::info("Server shutdown complete");
        global_server = nullptr;

        return 0;

    } catch (const std::exception& e) {
        spdlog::error("Fatal error: {}", e.what());
        return 1;
    }
}
