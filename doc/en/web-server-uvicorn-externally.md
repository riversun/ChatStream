# uvicorn (External Launch)

If you want to launch `example_server_redpajama_simple.py` in `./example` as a server,

```shell
uvicorn example.web_server_redpajama_simple.py:app --host 0.0.0.0 --port 3000
```

## uvicorn launch options

https://www.uvicorn.org/settings/



## Source Code

**example_server_redpajama_simple.py**

```python
import torch
import uvicorn
from fastapi import FastAPI, Request
from fastsession import FastSessionMiddleware, MemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM

from chatstream import ChatStream, ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"
device = "cuda"  # "cuda" / "cpu"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=2,
    max_queue_size=5,
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

app = FastAPI()

app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",  # Key for cookie signature
                   store=MemoryStore(),  # Store for session saving
                   http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
                   secure=True,  # False: For local development env. True: For production. Requires Https
                   )


@app.post("/chat_stream")
async def stream_api(request: Request):
    # handling FastAPI/Starlette's Request
    response = await chat_stream.handle_chat_stream_request(request)
    return response


@app.on_event("startup")
async def startup():
    # start request queueing system
    await chat_stream.start_queue_worker()
```

