import asyncio

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import set_seed
from chatstream import ChatStream, ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt, LoadTime

# Fix seed value for verification.
seed_value = 42
set_seed(seed_value)

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"

device = "cuda"  # "cuda" / "cpu"

# use loadtime for loading progress
model = LoadTime(name=model_path,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()

# model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)

tokenizer = AutoTokenizer.from_pretrained(model_path)

if device == "cuda":
    model.to(device)

chat_stream = ChatStream(
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
    # add_special_tokens=False,
    top_p=0.7,
    top_k=50,
    temperature=0.7
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
