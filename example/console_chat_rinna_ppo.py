import asyncio

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import set_seed
from chatstream import ChatStream, ChatPromptRinnaJapaneseGPTNeoxInst as ChatPrompt, LoadTime

device = "cuda"  # "cuda" / "cpu"

model_path = 'rinna/japanese-gpt-neox-3.6b-instruction-ppo'

model = LoadTime(name=model_path, hf=True,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()
# model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)

tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)

if device == "cuda":
    model.to(device)

chat_stream = ChatStream(
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
    add_special_tokens=False,
    max_new_tokens=256,  # The maximum size of the newly generated tokens
    context_len=1024,  # The size of the context (in terms of the number of tokens)
    temperature=1.0,  # The temperature value for randomness in prediction
    top_k=50,  # Value of top K for sampling
    top_p=1.0,  # Value of top P for sampling
)

# Fix seed value for verification.
seed_value = 42
set_seed(seed_value)


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
