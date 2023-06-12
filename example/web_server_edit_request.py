import torch
import uvicorn
from fastapi import FastAPI, Request
from fastsession import FastSessionMiddleware, MemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM

from chatstream import ChatStream, ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt, LoadTime
import logging
import json
import sys, traceback

"""
ChatStream web server for development use. View logs, allow HTTP, CORS with reduced security
"""

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"
device = "cuda"  # "cuda" / "cpu"

# use loadtime for loading progress
model = LoadTime(name=model_path,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()

# model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)

tokenizer = AutoTokenizer.from_pretrained(model_path)

model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=2,
    max_queue_size=5,
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

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


@app.post("/clear_context")
async def clear_api(request: Request):
    """
    Web API for clear chat history
    :param request:
    :return:
    """
    try:
        session_mgr = getattr(request.state, "session", None)
        if session_mgr:
            session_mgr.clear_session()

        return {"success": True}
    except Exception as e:
        tb = traceback.format_exc()
        sys.stderr.write(tb)
        return {"success": False}


@app.post("/chat_stream")
async def stream_api(request: Request):
    request_body = await request.body()
    data = json.loads(request_body)

    user_input = data["user_input"]
    regenerate = data["regenerate"] == "True"

    print(f"user_input:{user_input} regenerate:{regenerate}")

    session_mgr = getattr(request.state, "session", None)

    if session_mgr:
        session = session_mgr.get_session()
        chat_prompt = session.get("chat_prompt")  # get chat_prompt

    def callback_func(req, message):
        # called when streaming ended
        session_mgr = getattr(req.state, "session", None)
        if session_mgr:
            session = session_mgr.get_session()
            chat_prompt = session.get("chat_prompt")
            # show prompt on server
            print(chat_prompt.create_prompt())

    response = await chat_stream.handle_chat_stream_request(request, request_body, callback=callback_func)

    return response


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
