# CORS ミドルウェアの設定

チャットUI開発時などローカルで ChatStream サーバーを実行する場合、 UIをホストするサーバーと、ChatStream サーバーのホスト/ポートが異なる場合があります

CORS ミドルウェアを FastAPI に設定して、クロスオリジンアクセスを緩和することができます

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 関連:セッションミドルウェアの設定

ローカル開発時には HTTPS でない場合があるため、同時にセッションミドルウェアの設定もローカル開発にあわせるため
開発時にかぎって以下のように `secure=False` にることができます

```python
from fastsession import FastSessionMiddleware, MemoryStore
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",
                   store=MemoryStore(),
                   http_only=True,
                   secure=False,
                   )
```

**参考**  
[セッションミドルウェア](middleware-session.md)
