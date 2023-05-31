import json
import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastsession import FastSessionMiddleware, MemoryStore


from chatstream import ChatStream,ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt

"""
An example of using mock responses instead of actual pre-trained models for verification.
Since pre-trained models take time to load, they should be used for client development, etc.
"""

chat_stream = ChatStream(
    use_mock_response=True,  # use dummy response for testing
    mock_params={"type": "echo", "initial_wait_sec": 1, "time_per_token_sec": 1},
    chat_prompt_clazz=ChatPrompt,
)
chat_stream.logger.setLevel(logging.DEBUG)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Add session middleware to keep context
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",  # Key for cookie signature
                   store=MemoryStore(),  # Store for session saving
                   http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
                   secure=False,  # False: For local development env. True: For production. Requires Https
                   )


@app.post("/chat_stream")
async def stream_api(request: Request):

    # インターセプトする場合
    request_body = await request.body()
    data = json.loads(request_body)

    user_input = data["user_input"]
    regenerate = data["regenerate"] == "True"

    def callback_func(req, message):
        print(f"文章生成処理が終わりました message:{message}")
        # セッションマネージャを取得する
        session_mgr = getattr(request.state, "session", None)

        # セッションオブジェクト（辞書オブジェクト）を取得する
        session = session_mgr.get_session()
        chat_prompt = session.get("chat_prompt")
        print(chat_prompt.create_prompt())

        pass

    response = await chat_stream.handle_starlette_request(request, request_body, callback=callback_func)

    return response


@app.on_event("startup")
async def startup():
    await chat_stream.start_queue_worker()


def start_server():
    uvicorn.run(app, host='localhost', port=9999)


def main():
    start_server()


if __name__ == "__main__":
    main()
