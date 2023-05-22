import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastsession import FastSessionMiddleware, MemoryStore

from chat_prompt_for_redpajama_incite import ChatPromptRedpajamaIncite as ChatPrompt
from chatstream import ChatStream

MAX_CONCURRENT_CONNECTIONS = 2
MAX_QUEUE_SIZE = 5

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"

device = "cuda"  # "cuda" / "cpu"
tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
if device == "cuda":
    model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=MAX_CONCURRENT_CONNECTIONS,
    max_queue_size=MAX_QUEUE_SIZE,
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

app = FastAPI()

# Add session middleware to keep context
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",  # Key for cookie signature
                   store=MemoryStore(),  # Store for session saving
                   http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
                   secure=False,  # False: For local development env. True: For production. Requires Https
                   )


@app.post("/chat_stream")
async def stream_api(request: Request):
    response = await chat_stream.handle_starlette_request(request)
    return response


@app.get("/stats")
async def stats_api():
    return chat_stream.get_stats()


# for absolute URL of html contained dir
def get_html_dir():
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), 'html')


app.mount("/", StaticFiles(directory=get_html_dir(), html=True), name="html")


@app.on_event("startup")
async def startup():
    await chat_stream.start_queue_worker()


def start_server():
    uvicorn.run(app, host='localhost', port=18080)


def main():
    start_server()


if __name__ == "__main__":
    main()
