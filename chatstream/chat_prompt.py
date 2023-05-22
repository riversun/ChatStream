from abc import ABC, abstractmethod


class ChatContent:
    def __init__(self, role: str, msg: str = ""):
        self.role = role
        self.message = msg

    def get_role(self):
        return self.role

    def get_message(self):
        return self.message

    def set_message(self, msg):
        self.message = msg

    def __dict__(self):
        return {"role": self.role, "message": self.message}

    @classmethod
    def from_dict(cls, data):
        return cls(data["role"], data["message"])


class AbstractChatPrompt(ABC):
    """
    A builder to build chat prompts according to the characteristics of each language model.
    """

    def __init__(self):
        self.system = ""
        self.chat_contents = []
        self.responder_messages = []
        self.requester_messages = []
        self.requester = ""
        self.responder = ""
        self.chat_mode = True

    def get_turn(self):
        return len(self.requester_messages)

    def set_chat_mode_enabled(self, enabled):
        self.chat_mode = enabled

    def is_chat_mode_enabled(self):
        return self.chat_mode

    def set_system(self, system):
        """
        Set initial prompts for "system."
        :param system:
        :return:
        """
        self.system = system

    def set_requester(self, requester):
        """
        Sets the role name of the requester (=user)
        :param requester:
        :return:
        """
        self.requester = requester

    def set_responder(self, responder):
        """
        Sets the role name of the responder (=AI)
        :param responder:
        :return:
        """
        self.responder = responder

    def add_requester_msg(self, message):
        self._add_msg(ChatContent(role=self.requester, msg=message))

    def add_responder_msg(self, message):
        self._add_msg(ChatContent(role=self.responder, msg=message))

    def set_responder_last_msg(self, message):
        """
        AI 側の最新メッセージを更新する
        """

        # responder_messagesリストの最後のメッセージを更新
        self.responder_messages[-1].message = message

    def get_responder_last_msg(self):
        """
        AI側の最新メッセージを取得する
        """
        return self.responder_messages[-1].message

    def get_requester_last_msg(self):
        """
        Retrieve the latest message from the requester
        :return:
        """
        return self.requester_messages[-1].message

    def _add_msg(self, msg):
        self.chat_contents.append(msg)
        if msg.role == self.responder:
            self.responder_messages.append(msg)
        elif msg.role == self.requester:
            # If necessary, replace line breaks, etc. in the input string with tokens understood by the tokenizer.
            # ユーザーによる入力を置換指定された条件で置換する
            if self.get_replacement_when_input() is not None:
                final_msg_str = self.replace_string(msg.get_message(), self.get_replacement_when_input())
            else:
                final_msg_str=msg.get_message()

            msg.set_message(final_msg_str)
            self.requester_messages.append(final_msg_str)

    def is_requester_role(self, role):
        if self.requester == role:
            return True
        else:
            return False

    def get_skip_len(self,omit_last_message=False):
        """
        （Get the length to skip (already entered as a prompt)
        :return:
        """
        current_prompt = self.create_prompt(omit_last_message=omit_last_message) # end_point はメッセージ履歴の最後から何番目までを取得するか。Noneの場合はすべて。
        #print(f"#get_skip_len end_point:{end_point} crr_prompt:{current_prompt}")

        skip_echo_len = len(current_prompt)
        return skip_echo_len

    def replace_string(self, original_string, replace_list):
        """
        original_string を replace_list にある置換ペア（タプル）にしたがって置換する
        replace_list =[("A","B"),("C","D")] replace A with B and replace C with D
        """
        if replace_list is None:
            return original_string
        for old, new in replace_list:
            original_string = original_string.replace(old, new)
        return original_string

    def __dict__(self):
        return {
            "system": self.system,
            "chat_contents": [chat_content.__dict__() for chat_content in self.chat_contents],
            "responder_messages": [responder_message.__dict__() for responder_message in self.responder_messages],
            "requester_messages": [requester_message.__dict__() for requester_message in self.requester_messages],
            "requester": self.requester,
            "responder": self.responder,
            "chat_mode": self.chat_mode,
        }

    @classmethod
    def from_dict(cls, data):
        chat_prompt = cls()
        chat_prompt.system = data["system"]
        chat_prompt.chat_contents = [ChatContent.from_dict(chat_content_data) for chat_content_data in
                                     data["chat_contents"]]
        chat_prompt.responder_messages = [ChatContent.from_dict(responder_message_data) for responder_message_data in
                                          data["responder_messages"]]
        chat_prompt.requester_messages = [ChatContent.from_dict(requester_message_data) for requester_message_data in
                                          data["requester_messages"]]
        chat_prompt.requester = data["requester"]
        chat_prompt.responder = data["responder"]
        chat_prompt.chat_mode = data["chat_mode"]
        return chat_prompt

    @abstractmethod
    def get_stop_strs(self):
        pass

    @abstractmethod
    def create_prompt(self,omit_last_message=False):
        pass

    def get_replacement_when_input(self):
        """
        ユーザーからの入力文字列を指定した置換ルールにしたがって置換する
        """
        return None

    def get_replacement_when_output(self):
        """
        モデルからの逐次出力トークンを置換ルールにしたがって置換する
        """
        return None
