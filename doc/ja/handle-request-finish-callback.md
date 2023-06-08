# チャットストリームの送出完了のコールバックを受け取る

ChatStream では、ストリーミングレスポンスを行うため、エンドポイントで `return reponse` を行ったタイミングが文章生成処理の終了ではありません。

そこで、文章生成の完了のタイミングをキャッチしたい場合、
エンドポイントの実装で、 `handle_chat_stream_request` の引数 `callback` にコールバック関数を指定します。

文章生成が完了すると、指定したコールバック関数が呼び出されます

```python
@app.post("/chat_stream")
async def stream_api(request: Request):

    def callback_func(request, message):
        # 文章生成が終了したとき
        
        # ここでは、セッションに格納されている ChatPrompt を取得して、これまでの会話履歴をもとにプロンプトを生成する例
        session_mgr = getattr(request.state, "session", None)
        session = session_mgr.get_session()
        chat_prompt = session.get("chat_prompt")
        print(chat_prompt.create_prompt())

    pass

    response = await chat_stream.handle_chat_stream_request(request, callback=callback_func)

    return response
```

### 文章生成終了時のコールバック関数のパラメータ message の取り得る値と意味

|message の値|説明|
|:----|:----|
|success|ストリームがクライアントに向け正常に送出された|
|client_disconnected_while_streaming|ストリーム送出中にクライアントから切断された|
|client_disconnected_before_streaming|ストリーム送出前にクライアントから切断されていた|
|unknown_error_occurred|ストリーム送出中に予期せぬエラーが発生した|
