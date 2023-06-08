# Receiving a Callback upon Completion of Chat Stream Transmission

In ChatStream, because we perform a streaming response, the timing of `return response` in the endpoint does not signify the completion of text generation.

Therefore, if you want to catch the timing of the completion of text generation, specify a callback function in the argument `callback` of `handle_chat_stream_request` in the implementation of the endpoint.

When the text generation is completed, the specified callback function will be called.

```python
@app.post("/chat_stream")
async def stream_api(request: Request):

    def callback_func(request, message):
        # When text generation is completed
        
        # Here, as an example, we retrieve the ChatPrompt stored in the session and generate a prompt based on the past conversation history.
        session_mgr = getattr(request.state, "session", None)
        session = session_mgr.get_session()
        chat_prompt = session.get("chat_prompt")
        print(chat_prompt.create_prompt())

    pass

    response = await chat_stream.handle_chat_stream_request(request, callback=callback_func)

    return response
```

### Possible Values and Meanings of the Parameter `message` in the Callback Function at the Time of Text Generation Completion

|Value of `message`|Explanation|
|:----|:----|
|success|The stream was successfully sent to the client|
|client_disconnected_while_streaming|The client disconnected during the stream transmission|
|client_disconnected_before_streaming|The client had disconnected before the stream transmission|
|unknown_error_occurred|An unexpected error occurred during the stream transmission|