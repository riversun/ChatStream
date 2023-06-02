import json
import logging

import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastsession import FastSessionMiddleware, MemoryStore

from chatstream import ChatStream, ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt

"""
An example of using mock responses instead of actual pre-trained models for verification.
Since pre-trained models take time to load, they should be used for client development, etc.
"""

local_development_weak_security = True

chat_stream = ChatStream(
    use_mock_response=True,  # use dummy response for testing
    mock_params={"type": "round",  # "echo" "round" "long"
                 "initial_wait_sec": 0.3,
                 "time_per_token_sec": 0.2},
    chat_prompt_clazz=ChatPrompt,
)
chat_stream.logger.setLevel(logging.DEBUG)

app = FastAPI()

if local_development_weak_security:
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
                   secure=not local_development_weak_security,
                   # False: For local development env. True: For production. Requires Https
                   )


@app.post("/chat_stream")
async def stream_api(request: Request):
    # intercept request
    request_body = await request.body()
    data = json.loads(request_body)

    user_input = data["user_input"]
    regenerate = data["regenerate"] == "True"

    # receive when finished streaming
    def callback_func(req, message):
        print(f"Streaming generation finished message:{message}")
        session_mgr = getattr(req.state, "session", None)
        session = session_mgr.get_session()
        chat_prompt = session.get("chat_prompt")
        print(chat_prompt.create_prompt())

    response = await chat_stream.handle_starlette_request(request, request_body, callback=callback_func)

    return response


@app.post("/clear_context")
async def clear_api(request: Request):
    return await chat_stream.handle_clear_context_request(request)


@app.get("/chatstream.js")
def index(response: Response):
    return chat_stream.js(response)


@app.get("/")
def index(response: Response):
    ui_init_params = {
        "developMode": True,
        "clearContextOnReload": True,
        "welcomeMessage": "ようこそ!私はAIアシスタントです。なんでも聞いてください",
        "style_name": "casual_white",
        "style_opts": {
            "show_ai_icon": True,
            "show_human_icon": True,
            "show_human_icon_on_input": True,
            "ai_icon_url": "https://riversun.github.io/chatstream/img/icon_ai_00.png",
            "human_icon_url": "https://riversun.github.io/chatstream/img/icon_human_00.png",
            "regenerate_enabled": True,
            "button_label_stop_generating": "文章生成停止",
            "button_label_regenerate": "レスポンスを再生成",
            "label_input_placeholder": "メッセージを入力してください",
        }
    }

    return chat_stream.index(response, opts={"ui_init_params": ui_init_params})


@app.on_event("startup")
async def startup():
    await chat_stream.start_queue_worker()


def start_server():
    uvicorn.run(app, host='localhost', port=9999)


def main():
    start_server()


if __name__ == "__main__":
    main()
