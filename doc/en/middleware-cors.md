# Setting Up CORS Middleware

When running a ChatStream server locally, such as during chat UI development, the host/server and port of the ChatStream server may differ from that of the server hosting the UI.

By setting up CORS middleware in FastAPI, you can mitigate cross-origin access.

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

## Related: Setting up Session Middleware

During local development, there may be cases where HTTPS is not used. Therefore, to adapt the session middleware settings to local development, you can set `secure=False` for development only, as follows:

```python
from fastsession import FastSessionMiddleware, MemoryStore
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",
                   store=MemoryStore(),
                   http_only=True,
                   secure=False,
                   )
```

**Reference**  

[Session Middleware](middleware-session.md)