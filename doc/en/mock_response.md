# Using Mock Responses (Fast Startup)

Using mock responses allows you to generate dummy sentences instead of loading time-consuming pre-trained language models.

## Usage

```python
chat_stream = ChatStream(
    use_mock_response=True,
    mock_params={"type": "echo", "initial_wait_sec": 1, "time_per_token_sec": 1},
    chat_prompt_clazz=ChatPrompt,
)
```

Constructor arguments for the ChatStream class:

- **use_mock_response** ... Enable mock responses by setting this to True.
- **mock_params** ... Specifies the generation rules for mock responses.
- **chat_prompt_clazz** ... Class for managing prompt history.

**mock_params** parameters:

|Parameter|Parameter Value|Description|
|:----|:----|:----|
|type|round|Generates dummy sentences of about 100 words in a round-robin manner.|
| |long|Generates long dummy sentences.|
| |echo|Returns the string input by the user as is.|
|initial_wait_sec|Number (seconds)|Specifies the waiting time in seconds before sentence generation starts.|
|time_per_token_sec|Number (seconds)|Time to generate per token.|
