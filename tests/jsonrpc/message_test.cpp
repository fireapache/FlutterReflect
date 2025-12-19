#include <gtest/gtest.h>
#include "jsonrpc/message.h"

using namespace jsonrpc;

TEST(JsonRpcMessage, ParseValidRequest) {
    std::string json = R"({
        "jsonrpc": "2.0",
        "method": "test_method",
        "params": {"key": "value"},
        "id": 1
    })";

    auto request = Request::parse(json);
    EXPECT_EQ(request.jsonrpc, "2.0");
    EXPECT_EQ(request.method, "test_method");
    EXPECT_TRUE(request.hasId());
    EXPECT_EQ(request.getIdString(), "1");
}

TEST(JsonRpcMessage, ParseRequestWithStringId) {
    std::string json = R"({
        "jsonrpc": "2.0",
        "method": "test",
        "id": "test-id-123"
    })";

    auto request = Request::parse(json);
    EXPECT_TRUE(request.hasId());
    EXPECT_EQ(request.getIdString(), "test-id-123");
}

TEST(JsonRpcMessage, ParseNotification) {
    std::string json = R"({
        "jsonrpc": "2.0",
        "method": "notification_method",
        "params": {}
    })";

    auto request = Request::parse(json);
    EXPECT_FALSE(request.hasId());
}

TEST(JsonRpcMessage, SerializeRequest) {
    Request req;
    req.method = "test_method";
    req.params = {{"key", "value"}};
    req.id = 42;

    std::string json = req.serialize();
    EXPECT_NE(json.find("test_method"), std::string::npos);
    EXPECT_NE(json.find("\"id\":42"), std::string::npos);
}

TEST(JsonRpcMessage, CreateSuccessResponse) {
    nlohmann::json result = {{"status", "ok"}};
    auto response = Response::success(result, 1);

    EXPECT_TRUE(response.result.has_value());
    EXPECT_FALSE(response.isError());
}

TEST(JsonRpcMessage, CreateErrorResponse) {
    auto error = Error::fromCode(ErrorCode::MethodNotFound, "Method not found");
    auto response = Response::errorResponse(error, 1);

    EXPECT_TRUE(response.isError());
    EXPECT_TRUE(response.error.has_value());
    EXPECT_EQ(response.error->code, -32601);
}

TEST(JsonRpcMessage, CreateNotification) {
    auto notif = Notification::create("test_notification", {{"data", 123}});
    EXPECT_EQ(notif.method, "test_notification");

    std::string json = notif.serialize();
    EXPECT_NE(json.find("test_notification"), std::string::npos);
}

TEST(JsonRpcMessage, ValidationFailsForInvalidVersion) {
    nlohmann::json j = {
        {"jsonrpc", "1.0"},  // Invalid version
        {"method", "test"}
    };

    EXPECT_THROW(validateJsonRpc(j), std::exception);
}

TEST(JsonRpcMessage, ValidationFailsForMissingMethod) {
    nlohmann::json j = {
        {"jsonrpc", "2.0"}
        // Missing method
    };

    EXPECT_THROW(validateJsonRpc(j), std::exception);
}
