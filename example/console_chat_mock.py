import asyncio
from chatstream import ChatStream,ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt

model = None
tokenizer = None
device = None

chat_stream = ChatStream(
    use_mock_response=True,
    mock_type="round",
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
