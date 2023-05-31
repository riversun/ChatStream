from chatstream import AbstractChatPrompt


class ChatPromptRinnaJapaneseGPTNeoxInst(AbstractChatPrompt):
    """
    https://huggingface.co/rinna/japanese-gpt-neox-3.6b-instruction-sft
    """

    def __init__(self):
        super().__init__()  # Call the initialization of the base class
        self.set_requester("ユーザー")
        self.set_responder("システム")

    def get_stop_strs(self):
        if not self.chat_mode:
            return None
        return []

    def get_replacement_when_input(self):
        return [("\n", "<NL>")]

    def get_replacement_when_output(self):
        return [("<NL>", "\n")]

    def create_prompt(self,opts={}):
        if self.chat_mode == False:
            return self.get_requester_last_msg()

        # Chat Mode == True の場合のプロンプトを構築する
        ret = self.system;
        for chat_content in self.get_contents(opts):

            chat_content_role = chat_content.get_role()
            chat_content_message = chat_content.get_message()

            if chat_content_role:

                if chat_content_message:
                    merged_message = chat_content_role + ": " + chat_content_message + "<NL>"
                else:
                    merged_message = chat_content_role + ": "

                ret += merged_message

        return ret

    def build_initial_prompt(self, chat_prompt):
        # 初期プロンプトは実装しない
        pass
