# シンプルなストリーミングチャットサーバー構築

ChatStream を使ったサーバー構築はシンプルです。

## パッケージのインポート

```python
from chatstream import ChatStream
```

## HFモデルの読み込み

HuggingFace モデルを指定して読み込みます

これはごく一般的なアプローチと同じです

```python
model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"
device = "cuda"  # "cuda" / "cpu"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)
```


## ChatStream インスタンスの作成

ChatStream インスタンスを作成します。


```python
chat_stream = ChatStream(
    num_of_concurrent_executions=2,
    max_queue_size=5,
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

```

コンストラクタのパラメータは以下の通りです

| パラメータ名                                                                     | パラメータ値                                                   | 説明                                        |
|:---------------------------------------------------------------------------|:---------------------------------------------------------|:------------------------------------------|
| num_of_concurrent_executions                                               | 整数値                                                      | 逐次トークン生成の同時処理数                            |
| max_queue_size                                                             | 整数値                                                      | トークン生成リクエストの待ち行列（キュー）サイズ                  |
| model                                                                      | HuggingFace Modelインスタンス                                  | HuggingFace Modelインスタンス                   |
| tokenizer                                                                  | HuggingFace Tokenizerインスタンス                              | HuggingFace Tokenizerインスタンス               |
| device                                                                     | 文字列                                                      | cuda" "cpu" "mps" など                      |
| chat_prompt_clazz | 	ChatPromptクラス	| モデルに対応したChatPrompt のクラス。（インスタンスではないので、注意) |

## FastAPI の初期化とミドルウェア登録

ChatStream ベースの Webアプリケーションにおいて、会話コンテクストを継続させるための方法の１つとして、
HTTP セッションを利用することができます。

ChatStream では、デフォルトで HTTP セッションを使うため、HTTP セッションを有効化するため、以下のようにセッション用ミドルウェアを有効にします。

これにより　会話履歴　を管理する ChatPrompt がセッションに保持されるようになり、Webチャットクライアントとのインタラクションがステートフルになります。

以下の実装例では、HTTP セッション保存先はメモリストアを指定しており、ユーザー毎の会話履歴はサーバー側でオンメモリに保持されます。


```python
from fastapi import FastAPI, Request
from fastsession import FastSessionMiddleware, MemoryStore

app = FastAPI()

app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",  # Key for cookie signature
                   store=MemoryStore(),  # Store for session saving
                   http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
                   secure=False,  # False: For local development env. True: For production. Requires Https
                   )
```

ユーザーと
なお、ChatPromptForModel クラス