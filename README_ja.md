# ChatStream

[English](https://github.com/riversun/ChatStream/blob/main/README.md) | [&#26085;&#26412;&#35486;](https://github.com/riversun/ChatStream/blob/main/README_ja.md)

**ChatStream** は **事前学習済大規模言語モデル** 向けのチャットツールキットです

FastAPI/Starlette ベースの Web アプリケーション/ Web API に組み込むことで、負荷コントロールを行いながら事前学習済言語モデルによる逐次文章生成を行うことができます。


## インストール

```
pip install chatstream
```

## クイックスタート

### 必要パッケージのインストール

```
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu117
pip install transformers
pip install "uvicorn[standard]" gunicorn 
```


### ChatStream サーバーの実装

事前学習済モデルのストリーミングチャットサーバーを実装します

```python
import torch
from fastapi import FastAPI, Request
from fastsession import FastSessionMiddleware, MemoryStore
from transformers import AutoTokenizer, AutoModelForCausalLM

from chatstream import ChatStream,ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"
device = "cuda"  # "cuda" / "cpu"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=2,# 文章生成の最大同時実行数
    max_queue_size=5,# 待ち行列の大きさ
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

app = FastAPI()

# ユーザーごとの ChatPrompt を HTTP セッションに保持するため、セッションミドルウェアを指定
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",
                   store=MemoryStore(),
                   http_only=True,
                   secure=False,
                   )


@app.post("/chat_stream")
async def stream_api(request: Request):
    # FastAPI の Request オブジェクトを `handle_chat_stream_request` に渡すだけで自動的にキューイング、同時実行制御します
    response = await chat_stream.handle_chat_stream_request(request)
    return response


@app.on_event("startup")
async def startup():
    # Webサーバー起動と同時に `start_queue_worker` を行い、キューイングシステムを開始します
    await chat_stream.start_queue_worker()

```

## 目次

- [ChatStreamとは](doc/ja/features.md)
- [プロンプトクラス ChatPrompt のインポート](doc/ja/chat-prompt.md)
- [モデルクラスの読み込み](doc/ja/load-hf-model.md)
- [HTTP セッションミドルウェアの設定](doc/ja/middleware-session.md)
- [ - ChatStream の生成と初期化](doc/ja/chatstream-initialize.md)



- Web API エンドポイントの実装
  - [- エンドポイントの実装](doc/ja/handle-request.md)
  - [ストリーミング送信完了のコールバックを受け取る](doc/ja/handle-request-finish-callback.md)
  - [ユーザーからのリクエストの読み取り](doc/ja/handle-request-intercept.md)
  - [ - HTTP セッションの設定方法](doc/ja/handle-request-session.md)


- キューイングシステムと同時処理制限
  - [キューイングシステムとは](doc/ja/queue-system.md)
  - [キューイングシステムの開始](doc/ja/queue-system-start.md)


- Web サーバー(ASGI server) の起動
  - [uvicorn (内部から起動)](doc/ja/web-server-uvicorn-internally.md)
  - [uvicorn (外部から起動)](doc/ja/web-server-uvicorn-externally.md)
  - [gunicorn](doc/ja/web-server-gunicorn.md)


- コンソールチャットの実装
  - [モデルの動作確認用に簡易的なコンソールチャットを実行する](doc/ja/console-chat.md)


- 開発時の設定
  - [CORS ミドルウェアの設定](doc/ja/middleware-cors.md)
  - [モックレスポンスの利用（高速起動）](doc/ja/mock_response.md)
  - [ロギングの設定](doc/ja/logging.md)
  - [再掲:ユーザーからのリクエストの読み取り](doc/ja/handle-request-intercept.md)
  - [時間のかかるモデル読み込みにプログレスバーをつける](doc/ja/load-model-with-pbar.md)


- 高度な設定
  - チャット履歴の永続化
    - [- カスタムリクエストハンドラの実装](doc/ja/request-handler-how-to.md)
  - 大規模アクセスを想定した構成
    - OAuth を使用したログイン認証との連携
    - [- マルチ GPU での負荷分散](doc/ja/multi-gpu.md)
    - [- マルチGPUサーバーでの負荷分散](doc/ja/multi-server.md)


# License

All code in this repository was developed by Tom Misawa except where otherwise noted.  Copyright (c) 2023, Tom Misawa.  All rights reserved. The code is licensed under the Apache 2.0 license.

```
Copyright 2023 Tom Misawa(riversun.org@gmail.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

# Citing ChatStream

```bibtex
@software{chatstream,
  title = {{ChatStream: A streaming chat toolkit for pre-trained large language models(LLM)}},
  author = {Tom Misawa(riversun.org@gmail.com) },
  url = {https://github.com/riversun/ChatStream}
  month = {5},
  year = {2023},
  version = {0.15},
}
```


