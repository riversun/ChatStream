# エンドポイントの実装

`/chat_stream` という URL パスに、ストリーミングチャット用のWebエンドポイントをつくるには
以下のように `handle_chat_stream_request` を呼び出します。

これだけで、ユーザーからのリクエストは　文章生成の同時実行数を制御したストリーミングチャットの実装は完了です
 
```python
@app.post("/chat_stream")
async def stream_api(request: Request):
    # handling FastAPI/Starlette's Request
    response = await chat_stream.handle_chat_stream_request(request)
    return response
```

#### このエンドポイントの実装内でクライアントからのリクエスト(Request)内容を読み取りたい場合は以下を参照してください

[ユーザーからのリクエストの読み取り](handle-request-intercept.md)

#### このエンドポイントの実装内でセッション変数にアクセスしたい場合は以下を参照してください
[ - handle-request-session.md](handle-request-session.md)


#### このエンドポイントの実装内で、文章生成の完了をキャッチしたい場合は以下を参照してください
[ストリーミング送信完了のコールバックを受け取る](handle-request-finish-callback.md)
  
