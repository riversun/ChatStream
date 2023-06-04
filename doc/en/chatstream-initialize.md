Here's the English version of your markdown:

# Generation and Initialization of ChatStream

The ChatStream class is the core of the ChatStream package. It receives a Request from FastAPI/Starlette and is responsible for sending a streaming response to the client while controlling the load.

Initialize it by specifying the model, tokenizer, device, the maximum number of concurrent executions `num_of_concurrent_executions`, the maximum size of the waiting queue `max_queue_size`, and the prompt class `ChatPrompt`.

```python
from chatstream import ChatStream
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=2,
    max_queue_size=5,
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)
```

## List of Options

List of initialization options (constructor arguments) for ChatStream.

|Parameter name|Description|
|:----|:----|
|model|A pre-trained language model in HuggingFace format.|
|tokenizer|A tokenizer in HuggingFace format.|
|device|Execution device. Choose from "cpu" / "cuda" / "mps".|
|num_of_concurrent_executions|The number of simultaneous text generation tasks in the pre-trained language model. Default is 2.|
|max_queue_size|The maximum queue size for text generation tasks in the pre-trained language model. Default is 5.|
|too_many_request_as_http_error|Whether to return status 429 when a 'Too many requests' situation occurs. Default is False.|
|use_mock_response|Whether to return a fixed phrase for testing. As it does not need to load the model, it starts up immediately. Default is False.|
|mock_params|The type of phrase to return when use_mock_response=True "round" / "long". Default is {"type": "round"}.|
|chat_prompt_clazz|The class that manages the prompt sent to the language model. Implement a class that generates a chat prompt according to the etiquette of each model, inheriting from AbstractChatPrompt.|
|max_new_tokens|The maximum size of newly generated tokens. Default is 256.|
|context_len|The size of the context (number of tokens). Default is 1024.|
|temperature|The temperature value of randomness in prediction. Default is 1.0.|
|top_k|The value of top K for sampling. Default is 50.|
|top_p|The value of top P for sampling. Default is 1.0.|
|repetition_penalty|Penalty for repetition. Default is None.|
|repetition_penalty_method|The method of calculating the penalty for repetition. Default is "multiplicative".|
|add_special_tokens|Option for the tokenizer. Default is None.|
|request_handler|Request handler. By default, a handler that easily retains the session.|
|logger|Logging object. Default is None.|

Example:

```python
from chatstream import ChatStream,SimpleSessionRequestHandler
chat_stream = ChatStream(
    model=None,  # A pre-trained language model in HuggingFace format
    tokenizer=None,  # A tokenizer in HuggingFace format
    device=None,  # Execution device "cpu" / "cuda" / "mps"
    num_of_concurrent_executions=2,
    # The number of simultaneous text generation tasks in the pre-trained language model
    max_queue_size=5,  # The maximum queue size for text generation tasks in the pre-trained language model
    too_many_request_as_http_error=False,  # Whether to return status 429 when a 'Too many requests' situation occurs
    use_mock_response=False,  # Whether to return a fixed phrase for testing
    mock_params={type: "round"},  # The type of phrase to return when use_mock_response=True "round" / "long"
    chat_prompt_clazz=None,  # The class that manages the prompt sent to the language model
    max_new_tokens=256,  # The maximum size of newly generated tokens
    context_len=1024,  # The size of the context (number of tokens)
    temperature=1.0,  # The temperature value of randomness in prediction
    top_k=50,  # The value of top K for sampling
    top_p=1.0,  # The value of top P for sampling
    repetition_penalty=None,  # Penalty for repetition
    repetition_penalty_method="multiplicative",  # The method of calculating the penalty for repetition
    add_special_tokens=None,  # Option for the tokenizer
    request_handler=SimpleSessionRequestHandler(),
    # Request handler. By default, a handler that easily retains the session
    logger=None,  # Logging object
)


```
