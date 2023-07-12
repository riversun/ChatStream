import logging

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastsession import FastSessionMiddleware, MemoryStore
from starlette.requests import Request

from chatstream import ChatStream, ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt
from chatstream.access_control.default_client_role_grant_middleware import DefaultClientRoleGrantMiddleware

"""
An example of using mock responses instead of actual pre-trained models for verification.
Since pre-trained models take time to load, they should be used for client development, etc.
"""

local_development_weak_security = True

chat_stream = ChatStream(
    use_mock_response=True,  # use dummy response for testing
    mock_params={"type": "round",  # "echo" "round" "long"
                 "initial_wait_sec": 0.3,
                 "time_per_token_sec": 0},#0.2},
    client_roles={
        "user": {
            "apis": {
                "allow": ["chat_stream", "clear_context", "set_feedback"],
                "auth_method": "nothing",
                "use_session": True,  # セッションベースの認証
            }
        },
        "developer": {
            "apis": {
                "allow": ["chat_stream",
                          "clear_context",

                          "get_prompt",
                          "set_generation_params",
                          ],
                "auth_method": "ui_pass_phrase",
                "ui_pass_phrase": "dev mode",
                "use_session": True,
                "enable_dev_tool": True,

            },
        },
        "admin": {
            "apis": {
                "allow": "all",
                "auth_method": "ui_pass_phrase",
                "ui_pass_phrase": "admin mode",
                "use_session": True,
                "enable_dev_tool": True,
            },
        },
        "server_default": {
            "apis": {
                "allow": ["get_load"],
                "auth_method": "nothing",
                "use_session": False,  # サーバーの場合はセッション使わない
            },
        },
        "server_admin": {
            "apis": {
                "allow": "all",
                "auth_method": "header_phrase",
                "header_phrase": "i am server",
                "use_session": False,  # サーバーの場合はセッション使わない
            },
        }
    },

    chat_prompt_clazz=ChatPrompt,
)
chat_stream.logger.setLevel(logging.DEBUG)

app = FastAPI()

chat_stream.append_middlewares(app, opts={
    "fast_session": {
        "secret_key": "chatstream-default-session-secret-key",
        "store": MemoryStore(),
    },
    "develop_mode": True
})

ui_init_params = {
    "developMode": True,  # True: ローカルPCでの起動など HTTPS の無い環境でも HTTP セッションが有効になる、また、クロスオリジンポリシーが緩和される
    "clearContextOnReload": True,  # True: ブラウザで Web UIをリロードすると、会話履歴がクリアされる
    "welcomeMessage": "ようこそ!私はAIアシスタントです。なんでも聞いてください",
    "style_name": "casual_white",  # チャットのデザイン、インタラクションのプリセット名
    "style_opts": {
        "show_ai_icon": False,
        "show_human_icon": True,
        "show_human_icon_on_input": True,
        "ai_icon_url": "https://riversun.github.io/chatstream/img/icon_ai_00.png",
        "human_icon_url": "https://riversun.github.io/chatstream/img/icon_human_00.png",
        "regenerate_enabled": True,
        "button_label_stop_generating": "文章生成停止",
        "button_label_regenerate": "レスポンスを再生成",
        "label_input_placeholder": "メッセージを入力してください",
        "debug_window_enabled": True,  # TODO 実装。
    }
}

# FastAPI に ChatStream サービス関連 エンドポイントパス(URLパス)を自動的にセットする
# 各 URLパスの具体的な内容は default_api_paths.py を参照
# chat_stream.append_apis(app, {"all": True,"web_ui_params": ui_init_params})
chat_stream.append_apis(app, {"exclude": ["set_feedback"], "web_ui_params": ui_init_params})


@app.post("/set_feedback")
async def set_feedback_api(request: Request):
    # UIから　like/dislike ボタンでフィードバックをうけた内容をハンドリングする
    def fn_receive_feedback(feedback):
        print("フィードバックを受信しました")
        print(feedback)

    return await chat_stream.handle_set_feedback_request(request, {"on_feedback_received": fn_receive_feedback})


@app.on_event("startup")
async def startup():
    await chat_stream.start_queue_worker()


def start_server():
    uvicorn.run(app, host='localhost', port=9999)


def main():
    start_server()


if __name__ == "__main__":
    main()
