#pragma once

#include <string>
#include <functional>
#include <thread>
#include <mutex>
#include <memory>

namespace mcp {

/**
 * @brief Abstract base class for MCP transport layers
 * Handles message sending and receiving for MCP protocol
 */
class Transport {
public:
    virtual ~Transport() = default;

    /**
     * @brief Send a message through the transport
     * @param message JSON-RPC message to send
     */
    virtual void send(const std::string& message) = 0;

    /**
     * @brief Receive a message from the transport (blocking)
     * @return Received message, empty string if connection closed
     */
    virtual std::string receive() = 0;

    /**
     * @brief Check if transport is connected/ready
     */
    virtual bool isReady() const = 0;

    /**
     * @brief Close the transport
     */
    virtual void close() = 0;

    /**
     * @brief Set callback for when a message is received
     * Enables async message handling
     */
    virtual void setMessageCallback(std::function<void(const std::string&)> callback) {
        message_callback_ = std::move(callback);
    }

protected:
    std::function<void(const std::string&)> message_callback_;
};

/**
 * @brief STDIO transport for MCP
 * Reads from stdin and writes to stdout
 * Uses newline-delimited JSON for message framing
 */
class StdioTransport : public Transport {
public:
    StdioTransport();
    ~StdioTransport() override;

    void send(const std::string& message) override;
    std::string receive() override;
    bool isReady() const override;
    void close() override;

    /**
     * @brief Start async message receiving in background thread
     * Messages will be delivered via callback set with setMessageCallback
     */
    void startAsync();

    /**
     * @brief Stop async message receiving
     */
    void stopAsync();

private:
    bool ready_;
    bool async_running_;
    std::unique_ptr<std::thread> receive_thread_;
    std::mutex mutex_;

    void receiveLoop();
};

} // namespace mcp
