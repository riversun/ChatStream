# ChatStream

[English](https://github.com/riversun/ChatStream/blob/main/README.md) | [&#26085;&#26412;&#35486;](https://github.com/riversun/ChatStream/blob/main/README_ja.md)

**ChatStream** is a chat toolkit for **pre-trained large language models**.

It can be embedded in FastAPI/Starlette based web applications/web APIs to perform sequential sentence generation with pre-trained language models under load control.


## Installation

```
pip install chatstream
```

## Quick Start

### Install required packages

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
pip install transformers
pip install "uvicorn[standard]" gunicorn 
```


### Implementing a ChatStream server

Implement a streaming chat server for pre-trained models.

```python
import torch
from fastapi import FastAPI, Request
from fastsession import FastSessionMiddleware, MemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM

from chatstream import ChatStream,ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"
device = "cuda" # "cuda" / "cpu"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=2,# max_concurrent_executions for sentence generation
    max_queue_size=5,# size of queue
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

app = FastAPI()

# Specify session middleware to keep per-user ChatPrompt in the HTTP session
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",
                   store=MemoryStore(),
                   http_only=True,
                   secure=False,
                   )


@app.post("/chat_stream")
async def stream_api(request: Request):.
    # Just pass a FastAPI Request object to `handle_starlette_request` to automatically queue and control concurrency
    response = await chat_stream.handle_starlette_request(request)
    return response


@app.on_event("startup")
async def startup():.
    # start the queueing system by doing `start_queue_worker` at the same time the web server starts up
    await chat_stream.start_queue_worker()

```

## Table of Contents

- [What is ChatStream](doc/en/features.md)
- [ -- Importing Prompt Class ChatPrompt](doc/en/chat-prompt.md)
- [ -- Loading model classes](doc/en/load-hf-model.md)
- [ -- HTTP session middleware configuration](doc/en/middleware-session.md)
- [ -- Create and initialize ChatStream](doc/en/chatstream-initialize.md)



- Implementation of Web API Endpoints
  - [ -- Endpoint Implementation](doc/en/handle-request.md)
  - [ -- Receive streaming transmission completion callback](doc/en/handle-request-finish-callback.md)
  - [ -- Read requests from users](doc/en/handle-request-intercept.md)
  - [ -- How to set up an HTTP session](doc/en/handle-request-session.md)


- Queueing System and Concurrency Limit
  - [ -- What is the queueing system](doc/en/queue-system.md)
  - [ -- Starting the Queueing System](doc/en/queue-system-start.md)


- Start the Web server (ASGI server)
  - [ -- uvicorn (start from inside)](doc/en/web-server-uvicorn-internally.md)
  - [ -- uvicorn (start from outside)](doc/en/web-server-uvicorn-externally.md)
  - [ -- gunicorn](doc/en/web-server-gunicorn.md)


- Console chat implementation
  - [ -- Run a simple console chat to check the model behavior](doc/en/console-chat.md)


- Configuration during development
  - [ -- CORS middleware settings](doc/en/middleware-cors.md)
  - [ -- Using Mock Response (Fast Startup)](doc/en/mock_response.md)
  - [ -- Logging Settings](doc/en/logging.md)
  - [ -- Reading requests from users](doc/en/handle-request-intercept.md)
  - [ -- Attach progress bar to time-consuming model loading](doc/en/load-model-with-pbar.md)


- Advanced Settings
  - Chat History Persistence
    - [- Implement custom request handler](doc/en/request-handler-how-to.md)
  - Configuration for large scale access
    - Interfacing with login authentication using OAuth
    - [- Load Balancing on Multi-GPU](doc/en/multi-gpu.md)
    - [- Load Balancing with Multi-GPU Server](doc/en/multi-server.md)
