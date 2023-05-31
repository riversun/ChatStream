# メッセージインターセプト

FastAPI/Starlette を利用している場合、エンドポイントで `await request.body()` や `await request.json()` を実行すると、
リクエストストリームを消費(consume)してしまうため、 ChatStream にリクエストを委譲する前にリクエストをインターセプトをする場合は以下のように実装します


```python
import json
from fastapi import FastAPI, Request

@app.post("/chat_stream")
async def stream_api(request: Request):

    # Request を インターセプトする場合
    request_body = await request.body()
    data = json.loads(request_body)
    
    user_input = data["user_input"]
    regenerate = data["regenerate"]

    print(f"user_input:{user_input} regenerate:{regenerate}")
    
    # インターセプトした場合は `request_body` を指定する
    response = await chat_stream.handle_starlette_request(request, request_body)

    return response

```

 