import torch
import uvicorn
from fastapi import FastAPI, Request, Response
from fastsession import FastSessionMiddleware, MemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed

from chatstream import ChatStream, ChatPromptRinnaJapaneseGPTNeoxInst as ChatPrompt, LoadTime
import logging
import sys, traceback

from chatstream.access_control.default_client_role_grant_middleware import DefaultClientRoleGrantMiddleware

"""
ChatStream web server for development use. View logs, allow HTTP, CORS with reduced security
"""

num_gpus = 1
# device = "cpu"  # "cuda" / "cpu"
device = torch.device("cuda")

# model_path = 'rinna/japanese-gpt-neox-3.6b-instruction-ppo'
model_path = 'rinna/japanese-gpt-neox-3.6b-instruction-sft'

# model = LoadTime(name=model_path, hf=True,
#                  fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()

model = LoadTime(name=model_path, hf=True,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path))()  # , torch_dtype=torch.bfloat16

# model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)

tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

if device.type == 'cuda' and num_gpus == 1:
    model.to(device)

client_roless = {
    "develop": {
        "apis": {
            "allow": "all",
            "auth_method": "ui_pass_phrase",
            "ui_pass_phrase": "debug mode",
        },
    },

}

chat_stream = ChatStream(
    num_of_concurrent_executions=2,
    max_queue_size=5,
    model=model,
    tokenizer=tokenizer,
    num_gpus=num_gpus,
    device=device,
    chat_prompt_clazz=ChatPrompt,
    add_special_tokens=False,
    max_new_tokens=128,  # The maximum size of the newly generated tokens
    context_len=1024,  # The size of the context (in terms of the number of tokens)
    temperature=0.7,  # The temperature value for randomness in prediction
    top_k=10,  # Value of top K for sampling
    top_p=0.7,  # Value of top P for sampling
    client_roles={
        "user": {
            "apis": {
                "allow": ["chat_stream", "clear_context"],
                "auth_method": "nothing",  # default role
                "use_session": True,
            }
        },
        "admin": {
            "apis": {
                "allow": "all",
                "auth_method": "ui_pass_phrase",  # default role
                "ui_pass_phrase": "admin mode",
                "use_session": True,
                "enable_dev_tool":True,
            }
        },
    },  # client_roless,
    # allow_web_ui=True,  # WebUIを有効にする
    # allow_clear_context=True,  # コンテクストのクリアを許可する
    # allow_get_prompt=True,  # プロンプトの取得を許可する
    # allow_get_load=True,  # 負荷情報の取得を許可する
    # allow_set_generation_params=True,  # ユーザーごとに生成パラメータをセットできるようにする
    # allow_get_resource_usage=True,
    locale='en',
    # repetition_penalty=1.03,  # Penalty for repetition
    # repetition_penalty_method="multiplicative",  # Calculation method for repetition penalty
)

# Fix seed value for verification.
seed_value = 42
set_seed(seed_value)

chat_stream.logger.setLevel(logging.DEBUG)

app = FastAPI()

# from fastapi.middleware.cors import CORSMiddleware
#
# app.add_middleware(DefaultClientRoleGrantMiddleware, chat_stream=chat_stream)
#
# app.add_middleware(FastSessionMiddleware,
#                    secret_key="your-session-secret-key",  # Key for cookie signature
#                    store=MemoryStore(),  # Store for session saving
#                    http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
#                    secure=False,  # False: For local development env. True: For production. Requires Https
#                    )
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["X-ChatStream-API-DevTool-Enabled"],
# )

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
        "show_ai_icon": True,
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
chat_stream.append_apis(app, {"all": True, "web_ui_params": ui_init_params})


@app.on_event("startup")
async def startup():
    # start request queueing system
    await chat_stream.start_queue_worker()


def start_server():
    uvicorn.run(app, host='localhost', port=9999)


def main():
    start_server()


if __name__ == "__main__":
    main()
