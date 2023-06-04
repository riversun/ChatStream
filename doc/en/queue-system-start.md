# Starting the Queuing System

When using ChatStream, to enable functionality that supports multi-user concurrent access, you need to start the queuing system when FastAPI is initiated.

```python
@app.on_event("startup")
async def startup():
# start request queueing system
await chat_stream.start_queue_worker()
```

## See Also

[What is a Queuing System](queue-system.md)