#include "mcp/transport.h"
#include <iostream>
#include <sstream>
#include <thread>
#include <mutex>
#include <spdlog/spdlog.h>

#ifdef _WIN32
#include <io.h>
#include <fcntl.h>
#endif

namespace mcp {

StdioTransport::StdioTransport()
    : ready_(true), async_running_(false) {

#ifdef _WIN32
    // Set binary mode for stdin/stdout on Windows to prevent line ending translation
    _setmode(_fileno(stdin), _O_BINARY);
    _setmode(_fileno(stdout), _O_BINARY);
#endif

    spdlog::debug("STDIO transport initialized");
}

StdioTransport::~StdioTransport() {
    close();
}

void StdioTransport::send(const std::string& message) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (!ready_) {
        spdlog::error("Cannot send: transport not ready");
        return;
    }

    try {
        // Write message followed by newline (message framing)
        std::cout << message << std::endl;
        std::cout.flush();

        spdlog::debug("Sent message via STDIO: {} bytes", message.size());

    } catch (const std::exception& e) {
        spdlog::error("Error sending message: {}", e.what());
        ready_ = false;
    }
}

std::string StdioTransport::receive() {
    if (!ready_) {
        spdlog::error("Cannot receive: transport not ready");
        return "";
    }

    try {
        std::string line;
        if (std::getline(std::cin, line)) {
            // Remove any trailing whitespace
            while (!line.empty() && (line.back() == '\r' || line.back() == '\n')) {
                line.pop_back();
            }

            if (!line.empty()) {
                spdlog::debug("Received message via STDIO: {} bytes", line.size());
                return line;
            }
        }

        // EOF reached
        spdlog::info("EOF reached on stdin");
        ready_ = false;
        return "";

    } catch (const std::exception& e) {
        spdlog::error("Error receiving message: {}", e.what());
        ready_ = false;
        return "";
    }
}

bool StdioTransport::isReady() const {
    return ready_;
}

void StdioTransport::close() {
    spdlog::debug("Closing STDIO transport");
    stopAsync();
    ready_ = false;
}

void StdioTransport::startAsync() {
    if (async_running_) {
        spdlog::warn("Async receiving already running");
        return;
    }

    async_running_ = true;
    receive_thread_ = std::make_unique<std::thread>(&StdioTransport::receiveLoop, this);
    spdlog::info("Started async STDIO receiving");
}

void StdioTransport::stopAsync() {
    if (!async_running_) {
        return;
    }

    spdlog::debug("Stopping async STDIO receiving");
    async_running_ = false;

    if (receive_thread_ && receive_thread_->joinable()) {
        receive_thread_->join();
    }

    receive_thread_.reset();
    spdlog::info("Stopped async STDIO receiving");
}

void StdioTransport::receiveLoop() {
    spdlog::debug("STDIO receive loop started");

    while (async_running_ && ready_) {
        std::string message = receive();

        if (!message.empty() && message_callback_) {
            try {
                message_callback_(message);
            } catch (const std::exception& e) {
                spdlog::error("Error in message callback: {}", e.what());
            }
        }

        if (!ready_) {
            break;
        }
    }

    spdlog::debug("STDIO receive loop stopped");
}

} // namespace mcp
