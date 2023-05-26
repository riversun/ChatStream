import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastsession import FastSessionMiddleware, MemoryStore

from chat_prompt_for_redpajama_incite import ChatPromptRedpajamaIncite as ChatPrompt
from chatstream import ChatStream

"""
An example of using mock responses instead of actual pre-trained models for verification. 
Since pre-trained models take time to load, they should be used for client development, etc.
"""

chat_stream = ChatStream(
    use_mock_response=True,  # use dummy response for testing
    mock_params={"type": "round", "initial_wait_sec": 5, "time_per_token_sec": 1},
    chat_prompt_clazz=ChatPrompt,
)

app = FastAPI()

#

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
    response = await chat_stream.handle_starlette_request(request)
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
