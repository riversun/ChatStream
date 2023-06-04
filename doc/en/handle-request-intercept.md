# Message Interception

When using FastAPI/Starlette, if you execute `await request.body()` or `await request.json()` in the endpoint, it consumes the request stream. Therefore, if you want to intercept the request before delegating it to ChatStream, implement it as follows:

```python
import json
from fastapi import FastAPI, Request

@app.post("/chat_stream")
async def stream_api(request: Request):

    # When intercepting the Request
    request_body = await request.body()
    data = json.loads(request_body)
    
    user_input = data["user_input"]
    regenerate = data["regenerate"]

    print(f"user_input:{user_input} regenerate:{regenerate}")
    
    # If you intercept, specify `request_body`
    response = await chat_stream.handle_starlette_request(request, request_body)

    return response
```

