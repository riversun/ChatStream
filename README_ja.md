# ChatStream

事前学習済言語モデルを用いた大規模なストリーミングチャットサーバー用負荷コントロールユーティリティ

## インストール

```
pip install chatstream
```

## 何ができるの？

### ストリーミングチャット構築を簡単に

HuggingFace ベースの事前学習済の大規模言語モデルのストリーミングチャットを簡単に構築できる

**ストリーミングチャットとは**

大規模言語モデルで文章生成するとき、入力されたプロンプト（とこれまでの会話履歴）をもとに
次の文章をすべて生成してから出力する方式と、次の文章を１トークンずつ逐次出力する方式があるが。
後者の方式をとくに「ストリーミング」と呼ぶ。
本パッケージでは、トークン生成は1トークンごとに行われ、それをクライアントに対してストリーミングレスポンス（逐次送信）する。
これによりすべての文章が生成されるまで待たされるのにくらべ、ベターなユーザーエクスペリエンスの実現に寄与する

### 会話履歴の保持を自動的に行う

(デフォルトでは)HTTPセッション機能により、ユーザーと言語モデルとの会話履歴はサーバーサイドにオンメモリで持つ
セッションの持続時間は設定できるが、基本はブラウザが開いている間。
これにより、コンテクストが継続したマルチラウンドのWebチャットが可能となっている。
        
### 複数ユーザーの同時アクセス制御

複数クライアントからの同時アクセスを前提に設計されており、コンストラクタで指定された以下パラメータに従い制御される

```        
num_of_concurrent_executions: int ... 事前学習済言語モデルへの文章生成タスクの同時実行数
max_queue_size: int ... 文章生成の待ち行列（キュー）のサイズ。文章生成タスクの同時実行数がリミットを下回ったら
```

# 使い方

モデル用のプロンプトを生成する chat_prompt クラス(chat_prompt_for_redpajama_incite.py) と、ストリーミングサーバーの役割をもつ server.py を作成する

***chat_prompt_for_redpajama_incite.py**

```python
from chatstream.chat_prompt import AbstractChatPrompt


class ChatPromptRedpajamaIncite(AbstractChatPrompt):

    def __init__(self):
        super().__init__()  # Call the initialization of the base class
        self.set_requester("<human>")
        self.set_responder("<bot>")

    def get_stop_strs(self):
        """
        returns special stop strings for model to finsh generating sentence
        :return:
        """
        if not self.chat_mode:
            return None
        return [
            '<|endoftext|>',
            '\n<'
            # Safety stop valve when the model generates not only AI conversations but also human parts of the conversation.
        ]

    def create_prompt(self):
        """
        Build prompts according to the characteristics of each language model
        :return:
        """
        if self.chat_mode == False:
            return self.get_requester_last_msg()

        ret = self.system;
        for chat_content in self.chat_contents:
            chat_content_role = chat_content.get_role()
            chat_content_message = chat_content.get_message()
            if chat_content_role:
                if chat_content_message:
                    merged_message = chat_content_role + ": " + chat_content_message + "\n"
                else:
                    merged_message = chat_content_role + ":"
                ret += merged_message

        return ret


# portable UT
if False:
    chatPrompt = ChatPrompt()

    chatPrompt.set_requester("<human>")
    chatPrompt.set_responder("<bot>")
    chatPrompt.add_requester_msg("Who is Alan Turing")
    chatPrompt.add_responder_msg(None)

    assert """<human>: Who is Alan Turing
<bot>:""" == chatPrompt.create_prompt()

```

**server.py**

```python
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

```