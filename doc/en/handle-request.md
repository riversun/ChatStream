# Implementation of the Endpoint

To create a web endpoint for streaming chat at the URL path `/chat_stream`, call `handle_starlette_request` as shown below.

With this, the implementation of streaming chat, which controls the number of concurrent text generation requests from users, is complete.

```python
@app.post("/chat_stream")
async def stream_api(request: Request):
    # handling FastAPI/Starlette's Request
    response = await chat_stream.handle_starlette_request(request)
    return response
```

#### If you want to read the content of the client's request(Request) within this endpoint implementation, refer to the following:

[Reading User's Request](handle-request-intercept.md)

#### If you want to access session variables within this endpoint implementation, refer to the following:
[ - handle-request-session.md](handle-request-session.md)


#### If you want to catch the completion of text generation within this endpoint implementation, refer to the following:
[Receiving a Callback upon Completion of Streaming Transmission](handle-request-finish-callback.md)