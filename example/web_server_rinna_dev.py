import torch
import uvicorn
from fastapi import FastAPI, Request, Response
from fastsession import FastSessionMiddleware, MemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed

from chatstream import ChatStream, ChatPromptRinnaJapaneseGPTNeoxInst as ChatPrompt, LoadTime
import logging
import sys, traceback

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
    top_p=0.7,  # Value of top P for samplinga
    # allow_clear_context=True,  # コンテクストのクリアを許可する
    # allow_get_prompt=True,  # プロンプトの取得を許可する
    # allow_get_load=True,  # 負荷情報の取得を許可する
    # allow_web_ui=True,  # WebUIを有効にする
    # allow_set_generation_params=True,  # ユーザーごとに生成パラメータをセットできるようにする
    # allow_get_resource_usage=True,

    # repetition_penalty=1.03,  # Penalty for repetition
    # repetition_penalty_method="multiplicative",  # Calculation method for repetition penalty
)

# Fix seed value for verification.
seed_value = 42
set_seed(seed_value)

chat_stream.logger.setLevel(logging.DEBUG)

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",  # Key for cookie signature
                   store=MemoryStore(),  # Store for session saving
                   http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
                   secure=False,  # False: For local development env. True: For production. Requires Https
                   )


@app.post("/chat_stream")
async def stream_api(request: Request):
    def callback_func(req, message):
        session_mgr = getattr(req.state, "session", None)
        if session_mgr:
            session = session_mgr.get_session()
            chat_prompt = session.get("chat_prompt")
            print(f"Prompt:'{chat_prompt.create_prompt()}'")

    response = await chat_stream.handle_chat_stream_request(request, callback=callback_func)

    return response


@app.post("/clear_context")
async def clear_api(request: Request):
    return await chat_stream.handle_clear_context_request(request)


@app.get("/get_prompt")
async def get_prompt_api(request: Request):
    return await chat_stream.handle_get_prompt_request(request)



@app.get("/get_resource_usage")
async def get_prompt_api(request: Request):
    return await chat_stream.handle_get_resource_usage_request(request)


@app.get("/get_generation_params")
async def get_generation_params_api(request: Request):
    return await chat_stream.handle_get_generation_params_request(request)


@app.post("/set_generation_params")
async def set_generation_params_api(request: Request):
    return await chat_stream.handle_set_generation_params_request(request)


@app.get("/get_load")
async def set_generation_params_api(request: Request):
    return await chat_stream.handle_get_load_request(request)


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
            "debug_window_enabled": True,  # TODO 実装
        }
    }

    return chat_stream.index(response, opts={"ui_init_params": ui_init_params})


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
