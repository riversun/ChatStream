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

    def get_contents(self, opts={}):

        omit_last_message = opts.get("omit_last_message", False)

        list = []
        for idx, chat_content in enumerate(self.chat_contents):
            is_last = (idx == len(self.chat_contents) - 1)

            if omit_last_message and is_last:
                chat_content_role = chat_content.get_role()
                # chat_content_message = chat_content.get_message()
                last_content = ChatContent(role=chat_content_role, msg=None)
                list.append(last_content)
            else:
                list.append(chat_content)

        return list

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

    def get_responder_last_msg(self):
        """
        AI側の最新メッセージを取得する
        """
        return self.responder_messages[-1].message if self.responder_messages else None

    def get_requester_last_msg(self):
        """
        ユーザーからの最新メッセージを取得する
        """
        # ユーザーメッセージがあれば最新のものを、なければNoneを返す
        return self.requester_messages[-1].message if self.requester_messages else None

    def clear_last_responder_message(self):
        """
        Set the message of the last response from the responder (AI) to None.
        """
        if self.responder_messages and self.chat_contents and self.chat_contents[-1].get_role() == self.responder:
            self.responder_messages[-1].set_message(None)
            self.chat_contents[-1].set_message(None)
        else:
            pass

    def remove_last_requester_msg(self):
        """
        ユーザー側の最新メッセージを削除
        """
        if self.requester_messages and self.chat_contents and self.chat_contents[-1].get_role() == self.requester:
            self.requester_messages.pop()
            self.chat_contents.pop()

    def remove_last_responder_msg(self):
        """
        AI側の最新メッセージを削除
        """
        if self.responder_messages and self.chat_contents and self.chat_contents[-1].get_role() == self.responder:
            self.responder_messages.pop()
            self.chat_contents.pop()

    def set_responder_last_msg(self, message):
        """
        AI 側の最新メッセージを更新する
        """

        # responder_messagesリストの最後のメッセージを更新
        self.responder_messages[-1].message = message
        self.chat_contents[-1].set_message(message)

    def _add_msg(self, chat_content_obj):
        # チャットメッセージリストに追加
        self.chat_contents.append(chat_content_obj)
        if chat_content_obj.role == self.responder:
            self.responder_messages.append(chat_content_obj)
        elif chat_content_obj.role == self.requester:
            # If necessary, replace line breaks, etc. in the input string with tokens understood by the tokenizer.
            # ユーザーによる入力を置換指定された条件で置換する
            if self.get_replacement_when_input() is not None:
                final_msg_str = self.replace_string(chat_content_obj.get_message(), self.get_replacement_when_input())
            else:
                final_msg_str = chat_content_obj.get_message()

            chat_content_obj.set_message(final_msg_str)
            # requester メッセージリストに追加
            self.requester_messages.append(chat_content_obj)

    def is_requester_role(self, role):
        if self.requester == role:
            return True
        else:
            return False

    def get_skip_len(self, omit_last_message=False):
        """
        （Get the length to skip (already entered as a prompt)
        :return:
        """
        current_prompt = self.create_prompt({"omit_last_message":omit_last_message})

        skip_echo_len = len(current_prompt)

        return skip_echo_len

    def is_empty(self):
        """
        チャットプロンプトが空かどうかを確認する
        """
        return not self.requester_messages and not self.responder_messages

    def replace_string(self, original_string, replace_list):
        """
        original_string を replace_list にある置換ペア（タプル）にしたがって置換する
        replace_list =[("A","B"),("C","D")] の場合、
        original_string にある "A" は "B" に置換される。 "C" は "D" に置換される。
        replace A with B and replace C with D
        """
        if replace_list is None:
            return original_string
        for old, new in replace_list:
            original_string = original_string.replace(old, new)
        return original_string

    def __dict__(self):
        """
        シリアライズ
        データベースやファイルに保存用に。
        """
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
        """
        デシリアライズ
        データベース、ファイルからの復元
        """
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
    def create_prompt(self, opts):
        pass

    @abstractmethod
    def build_initial_prompt(self, chat_prompt_obj):
        """
        初期プロンプトを生成する
        """
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
