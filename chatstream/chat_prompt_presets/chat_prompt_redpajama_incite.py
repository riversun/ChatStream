from chatstream.chat_prompt import AbstractChatPrompt


class ChatPromptTogetherRedPajamaINCITEChat(AbstractChatPrompt):

    def __init__(self):
        super().__init__()  # Call the initialization of the base class
        self.set_requester("<human>")
        self.set_responder("<bot>")

    def get_stop_strs(self):
        if not self.chat_mode:
            return None

        # Chat Mode == True の場合の停止文字列を構築する
        return [
            '<|endoftext|>',
            '\n<'
            # Safety stop valve when the model generates not only AI conversations but also human parts of the conversation.
        ]

    def create_prompt(self, opts={}):
        """
        Build prompts according to the characteristics of each language model
        :return:
        """
        if self.chat_mode == False:
            return self.get_requester_last_msg()

        ret = self.system;
        for chat_content in self.get_contents(opts):
            chat_content_role = chat_content.get_role()
            chat_content_message = chat_content.get_message()
            if chat_content_role:
                if chat_content_message:
                    merged_message = chat_content_role + ": " + chat_content_message + "\n"
                else:
                    merged_message = chat_content_role + ":"
                ret += merged_message

        return ret

    def build_initial_prompt(self, chat_prompt):
        pass
        # If you want a common initial prompt for instructions, override this method and implement
        # chat_prompt.add_requester_msg("Do you know about the Titanic movie?")
        # chat_prompt.add_responder_msg("Yes, I am familiar with it.")
        # chat_prompt.add_requester_msg("Who starred in the movie?")
        # chat_prompt.add_responder_msg("Leonardo DiCaprio and Kate Winslet.")


# portable UT
if False:
    chatPrompt = ChatPromptRedPajamaINCITEChat()

    chatPrompt.set_requester("<human>")
    chatPrompt.set_responder("<bot>")
    chatPrompt.add_requester_msg("Who is Alan Turing")
    chatPrompt.add_responder_msg(None)

    print(f"{chatPrompt.create_prompt()}")
    assert """<human>: Who is Alan Turing
<bot>:""" == chatPrompt.create_prompt()
