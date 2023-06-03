# コンソールチャットの作成

`handle_console_input` メソッドを使用することで CLI ベースのチャットを簡単に作成しモデルを試すことができます

```python
import asyncio

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from chatstream import ChatStream, ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt, LoadTime

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"

device = "cuda"  # "cuda" / "cpu"

model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)

tokenizer = AutoTokenizer.from_pretrained(model_path)

if device == "cuda":
    model.to(device)

chat_stream = ChatStream(
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

async def console_chat_main():
    while True:
        user_input = input("YOU: ")
        if user_input.lower() == "exit":
            break

        async for response_text, updated_text, pos in chat_stream.handle_console_input(user_input):

            if pos == "begin":
                print("AI : ", end="", flush=True)
                print(updated_text, end="", flush=True)

            elif pos == "mid":
                print(updated_text, end="", flush=True)

            elif pos == "end":
                print()


if __name__ == "__main__":
    asyncio.run(console_chat_main())

```