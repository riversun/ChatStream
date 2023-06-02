import torch
import uvicorn
from fastapi import FastAPI, Request
from fastsession import FastSessionMiddleware, MemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM, set_seed

from chatstream import ChatStream, ChatPromptRinnaJapaneseGPTNeoxInst as ChatPrompt, LoadTime
import logging
import sys, traceback

"""
ChatStream web server for development use. View logs, allow HTTP, CORS with reduced security
"""

device = "cuda"  # "cuda" / "cpu"

# model_path = 'rinna/japanese-gpt-neox-3.6b-instruction-ppo'
model_path = 'rinna/japanese-gpt-neox-3.6b-instruction-sft'

model = LoadTime(name=model_path, hf=True,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()
# model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)

tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=2,
    max_queue_size=5,
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
    add_special_tokens=False,
    max_new_tokens=128,  # The maximum size of the newly generated tokens
    context_len=1024,  # The size of the context (in terms of the number of tokens)
    temperature=0.7,  # The temperature value for randomness in prediction
    top_k=10,  # Value of top K for sampling
    top_p=0.7,  # Value of top P for sampling
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

    response = await chat_stream.handle_starlette_request(request, callback=callback_func)

    return response


@app.post("/clear_context")
async def clear_api(request: Request):
    return await chat_stream.handle_clear_context_request(request)


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
