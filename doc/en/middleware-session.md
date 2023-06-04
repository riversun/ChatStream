# Session Middleware

In order to sustain multi-round conversations when conducting web chats with an open browser, the ChatPrompt (conversation history) needs to be updated throughout the multiple turns of conversation.

By default, ChatStream uses HTTP sessions to make the web application stateful, enabling it to retain the ChatPrompt as long as the browser is open.

To use HTTP sessions, register FastAPI's middleware as follows:

```python
from fastsession import FastSessionMiddleware, MemoryStore
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",
                   store=MemoryStore(),
                   http_only=True,
                   secure=True,
                   )
```

|Parameter|Description|
|:----|:----|
|secret_key|Key for signing cookies.|
|store|Store for saving sessions.|
|http_only|Determines whether the cookie cannot be accessed from client-side scripts (such as JavaScript). The default is True.|
|secure|False for local development environment. True for production environment. HTTPS is required.|

## Internal Process

In this default implementation, it generates a session ID, applies a signature to it, and then saves it in a cookie.

The cookie's storage period is only while the browser is open, and it's inaccessible from frontend JavaScript.

# Other Ways to Persist Conversation History

In the default implementation, the ChatPrompt exists in the session. The session information is managed in memory on the server side, and the session's duration is while the browser is open.

When constructing a full-fledged chat server, it is common to authenticate users and save ChatPrompts tied to users in a database (persist).

To carry out such processing, you can implement a [custom request handler](request-handler-how-to.md) and manage and persist the ChatPrompt on the request handler.

## Related: CORS Middleware

[CORS Middleware](middleware-cors.md)