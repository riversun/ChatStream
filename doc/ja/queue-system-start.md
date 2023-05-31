# キューイングシステムの開始

ChatStream を使用するときマルチユーザーの同時アクセスに対応した機能を有効にするためには
FastAPI が開始したときに、キューイングシステムを起動する必要があります

```python
@app.on_event("startup")
async def startup():
# start request queueing system
await chat_stream.start_queue_worker()
```

## 関連

[キューイングシステムとは](queue-system.md)
