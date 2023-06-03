# What is ChatStream
ChatStream is a toolkit for building scalable LLM streaming chat servers.

## 1. Easy to implement Streaming Chats

You can easily develop streaming chats with pre-trained large language models based on HuggingFace.

'Streaming Chat' refers to two ways of text generation with pre-trained language models: 


In HuggingFace's transformers library, these two methods of text generation with a large language model (LLM) are typically referred to as follows:

1. **Step-by-step token generation** : This method involves generating the next token of a sentence one at a time.

2. **Whole sentence generation** : This is typically done using a method called "decoding". 

Not only does step-by-step token generation allow for more control and interactivity during 
the generation process, but it also offers superior user experience in some cases as 
it allows for understanding the content of the sentence more quickly than whole sentence generation, 
due to the sequential generation of tokens.

|                                | Advantages                                 | Disadvantages                                                      |
|--------------------------------|--------------------------------------------|--------------------------------------------------------------------|
| Whole sentence generation                | Simple design                             | Users must wait until the sentence generation is finished. This can be particularly stressful when the server is busy and results are not produced. |
| Streaming Generation           | Does not require waiting for the entire sentence generation. | More complex design                                              |

This package performs token generation one token at a time, which is sent as a streaming response to the client. 

This contributes to a better user experience compared to waiting until the entire sentence is generated.

## 2. Keep conversation history, Allowing for Multi-round Conversations while Maintaining the Conversation Context

The conversation history between the user and the pre-trained language model is retained. 

By default, HTTP sessions are used, keeping the conversation while the browser is open. Depending on your needs, you can implement login functionality, persistent conversation contexts, etc.

## 3. Stable Chat Stream Generation During Multiple Concurrent Accesses

Designed with multiple concurrent client accesses in mind, it can be controlled according to the following parameters specified in the constructor.

```
num_of_concurrent_executions: int ... The number of simultaneous sentence generation tasks for the pre-trained language model
max_queue_size: int ... The size of the queue for sentence generation. If the number of concurrent sentence generation tasks falls below the limit, the request task is taken from the queue and the sentence generation task begins.
```

![img](https://riversun.github.io/chatstream/chatstream_queue.png)
