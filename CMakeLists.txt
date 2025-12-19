cmake_minimum_required(VERSION 3.20)
project(FlutterReflect VERSION 1.0.0 LANGUAGES CXX)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Build options
option(BUILD_TESTS "Build test suite" ON)
option(BUILD_EXAMPLES "Build example programs" ON)

# Windows-specific settings
if(WIN32)
    # Use static runtime to avoid DLL dependencies
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

    # Enable Unicode
    add_compile_definitions(UNICODE _UNICODE)
endif()

# Include FetchContent for dependency management
include(FetchContent)

# Dependency: nlohmann/json (JSON parsing)
FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
    GIT_SHALLOW TRUE
)

# Dependency: websocketpp (WebSocket client)
FetchContent_Declare(
    websocketpp
    GIT_REPOSITORY https://github.com/zaphoyd/websocketpp.git
    GIT_TAG 0.8.2
    GIT_SHALLOW TRUE
)

# Dependency: asio (Async I/O for WebSocket)
FetchContent_Declare(
    asio
    GIT_REPOSITORY https://github.com/chriskohlhoff/asio.git
    GIT_TAG asio-1-28-0
    GIT_SHALLOW TRUE
)

# Dependency: spdlog (Logging)
FetchContent_Declare(
    spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.12.0
    GIT_SHALLOW TRUE
)

# Make dependencies available
set(CMAKE_POLICY_DEFAULT_CMP0169 OLD)  # Allow FetchContent_Populate
FetchContent_MakeAvailable(nlohmann_json spdlog)

# Manually fetch websocketpp and asio (header-only libraries)
FetchContent_GetProperties(websocketpp)
if(NOT websocketpp_POPULATED)
    FetchContent_Populate(websocketpp)
    # Don't add_subdirectory, just use the headers
endif()

FetchContent_GetProperties(asio)
if(NOT asio_POPULATED)
    FetchContent_Populate(asio)
    # Don't add_subdirectory, just use the headers
endif()

# Source files
set(FLUTTER_REFLECT_SOURCES
    # JSON-RPC implementation
    src/jsonrpc/message.cpp
    src/jsonrpc/handler.cpp

    # MCP server
    src/mcp/server.cpp
    src/mcp/stdio_transport.cpp
    src/mcp/tool_registry.cpp

    # Flutter VM Service client
    src/flutter/vm_service_client.cpp
    src/flutter/widget_inspector.cpp
    src/flutter/widget_tree.cpp
    src/flutter/selector.cpp
    src/flutter/interaction.cpp
    src/flutter/instance_discovery.cpp
    src/flutter/app_launcher.cpp

    # MCP tools
    src/tools/connect_tool.cpp
    src/tools/get_tree_tool.cpp
    src/tools/find_tool.cpp
    src/tools/tap_tool.cpp
    src/tools/type_tool.cpp
    src/tools/scroll_tool.cpp
    src/tools/get_properties_tool.cpp
    src/tools/list_instances_tool.cpp
    src/tools/launch_tool.cpp
)

# Create library for reuse in tests
add_library(flutter_reflect_lib STATIC ${FLUTTER_REFLECT_SOURCES})

# Include directories
target_include_directories(flutter_reflect_lib PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${websocketpp_SOURCE_DIR}
    ${asio_SOURCE_DIR}/asio/include
)

# Link dependencies
target_link_libraries(flutter_reflect_lib PUBLIC
    nlohmann_json::nlohmann_json
    spdlog::spdlog
)

# Platform-specific linking
if(WIN32)
    target_link_libraries(flutter_reflect_lib PUBLIC ws2_32)
endif()

# Compile definitions
target_compile_definitions(flutter_reflect_lib PUBLIC
    ASIO_STANDALONE  # Use asio without Boost
    _WEBSOCKETPP_CPP11_INTERNAL_
)

# Main executable
add_executable(flutter_reflect src/main.cpp)
target_link_libraries(flutter_reflect PRIVATE flutter_reflect_lib)

# Windows console application settings
if(WIN32)
    set_target_properties(flutter_reflect PROPERTIES
        WIN32_EXECUTABLE FALSE
        OUTPUT_NAME "flutter_reflect"
    )
endif()

# Testing
if(BUILD_TESTS)
    enable_testing()

    # Google Test dependency
    FetchContent_Declare(
        googletest
        GIT_REPOSITORY https://github.com/google/googletest.git
        GIT_TAG v1.14.0
        GIT_SHALLOW TRUE
    )
    FetchContent_MakeAvailable(googletest)

    # Test sources
    set(TEST_SOURCES
        tests/jsonrpc/message_test.cpp
        tests/flutter/selector_test.cpp
    )

    add_executable(flutter_reflect_tests ${TEST_SOURCES})
    target_link_libraries(flutter_reflect_tests PRIVATE
        flutter_reflect_lib
        GTest::gtest_main
    )

    include(GoogleTest)
    gtest_discover_tests(flutter_reflect_tests)
endif()

# Examples
if(BUILD_EXAMPLES)
    add_executable(simple_connect examples/simple_connect.cpp)
    target_link_libraries(simple_connect PRIVATE flutter_reflect_lib)
endif()

# Installation rules
install(TARGETS flutter_reflect
    RUNTIME DESTINATION bin
)

# Print configuration summary
message(STATUS "FlutterReflect Configuration:")
message(STATUS "  Version: ${PROJECT_VERSION}")
message(STATUS "  Build type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  C++ standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build tests: ${BUILD_TESTS}")
message(STATUS "  Build examples: ${BUILD_EXAMPLES}")
message(STATUS "  Platform: ${CMAKE_SYSTEM_NAME}")
