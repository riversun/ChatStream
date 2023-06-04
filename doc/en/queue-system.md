# What is a Queuing System

ChatStream can queue requests and limit the number of sentence generations that can be executed simultaneously when a large number of concurrent access requests are received.

By limiting the number of concurrent sentence generation processes according to the performance of the GPU or CPU, you can achieve good response performance.

Moreover, if there are requests exceeding the concurrent execution limit, the system queues these requests (adds them to a waiting queue) and executes them sequentially, appropriately controlling the load.

## What is Concurrent Execution

In the case of execution on one GPU, it's not accurately "simultaneous execution" but "concurrent execution".

When the maximum number of concurrent executions is set, that many will be "concurrently executed".

For example, in a state where the maximum number of concurrent executions is set to 2, if two users, User 1 and User 2, request at the same timing, the requests of the two users will be added to the "processing queue" (a queue representing sentence generation in progress), generating sentences alternately for each token. In the case of a Japanese model, one token roughly corresponds to one character, so if one character is added to the sentence for User 1, one character will be added to the sentence for User 2. This is repeated until sentence generation is completed.

If User 3 interrupts in the middle, since the sentences for User 1 and User 2 are still being generated, the request of User C will be added to the "request queue" (waiting queue).

When the sentence generation of User 1 or User 2 is completed, the request of User 3, which is in the "request queue", will be added to the "processing queue", and the sentence generation process will begin.

![img](https://riversun.github.io/chatstream/chatstream_queue.png)


### Column: Asynchronous I/O and Concurrent Execution

    FastAPI supports asynchronous I/O, which has the ability to process multiple requests concurrently.
    Python's asynchronous I/O achieves concurrency using special functions called coroutines.
    In this case, concurrency means that only one task progresses at a time, but other tasks can progress while waiting for I/O operations (HTTP requests, token generation from the model, etc.). This form is called "cooperative multitasking".
    Each request is processed as a separate "asynchronous task", and these tasks can be switched on the same thread.
    In "asynchronous tasks", it may seem like multiple requests are concurrently accessing the model, but in reality, only one request is using the model at a given moment.
    Therefore, the period during which each request blocks for token generation by the model is limited, and in terms of sequential token output, control can be returned to other requests after generating a new token.
    Thus, during sentence generation by one request, all other requests are not blocked until the stop token or stop string appears, and each request can progress other requests while sequentially generating tokens from the model.

## Starting Queuing

By calling `start_queue_worker` at the startup of the web application, you can start the queue worker.

Starting the queue worker starts the request processing queue, and the queuing loop, which inserts requests into the request queue and sequentially executes them into the processing queue, begins.

`chatstream#start_queue_worker`
