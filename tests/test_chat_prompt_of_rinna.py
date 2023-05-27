import pytest

from chatstream import AbstractChatPrompt


class ChatPromptRinnaForTest(AbstractChatPrompt):

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

    def create_prompt(self, omit_last_message=False):
        if self.chat_mode == False:
            return self.get_requester_last_msg()

        # Chat Mode == True の場合のプロンプトを構築する
        ret = self.system;
        for i, chat_content in enumerate(self.chat_contents):
            chat_content_role = chat_content.get_role()
            chat_content_message = chat_content.get_message()

            if omit_last_message and (i == len(self.chat_contents) - 1):
                # omit_last_messageが有効で、今が最後のメッセージの場合
                chat_content_message = None  # 最後のメッセージパートは無効にする

            if chat_content_role:

                if chat_content_message:
                    merged_message = chat_content_role + ": " + chat_content_message + "<NL>"
                else:
                    merged_message = chat_content_role + ": "

                ret += merged_message

        return ret


class TestChatPromptRinna:

    @pytest.fixture
    def chat_prompt(self):
        chat_prompt = ChatPromptRinnaForTest()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg(None)
        return chat_prompt

    def test_turn(self, chat_prompt):
        assert chat_prompt.get_turn() == 2

    def test_chat_mode(self, chat_prompt):
        assert chat_prompt.is_chat_mode_enabled() == True

    def test_system(self, chat_prompt):
        assert chat_prompt.system == ""

    def test_requester(self, chat_prompt):
        assert chat_prompt.requester == "ユーザー"

    def test_responder(self, chat_prompt):
        assert chat_prompt.responder == "システム"

    def test_stop_strs(self, chat_prompt):
        assert chat_prompt.get_stop_strs() == []

    def test_create_prompt(self, chat_prompt):
        assert chat_prompt.create_prompt() == "ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: "

    def test_last_requester_message(self, chat_prompt):
        assert chat_prompt.get_requester_last_msg() == "渋谷の観光地を教えてください。"

    def test_last_responder_message(self, chat_prompt):
        assert chat_prompt.get_responder_last_msg() == None

    def test_last_msg(self):
        chat_prompt = ChatPromptRinnaForTest()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg("渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂")

        assert chat_prompt.get_requester_last_msg() == "渋谷の観光地を教えてください。"
        assert chat_prompt.get_responder_last_msg() == "渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂"

        assert chat_prompt.create_prompt() == "ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: 渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂<NL>"

    def test_remove_last_responder_message(self):
        chat_prompt = ChatPromptRinnaForTest()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg("渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂")

        # 削除前の最後のメッセージを取得
        last_msg_before = chat_prompt.get_responder_last_msg()

        # 最後のメッセージを削除
        chat_prompt.remove_last_responder_message()

        # 削除後の最後のメッセージを取得
        last_msg_after = chat_prompt.get_responder_last_msg() if chat_prompt.responder_messages else None

        # 削除前の最後のメッセージと削除後の最後のメッセージが違うことを確認
        assert last_msg_before != last_msg_after
        # 削除後の最後のメッセージが、削除前のものと違うか、あるいは応答者のメッセージがない場合はNoneであることを確認
        assert last_msg_after == (
            chat_prompt.responder_messages[-1].get_message() if chat_prompt.responder_messages else None)


        # 最後のメッセージを削除しようとする（リクエスターメッセージなので削除されないはず）
        chat_prompt.remove_last_responder_message()

        # 最後のリクエスタメッセージを確認
        last_requester_msg = chat_prompt.get_requester_last_msg()
        assert last_requester_msg =="渋谷の観光地を教えてください。"



        # 削除したあとでも もとの responder の最後のメッセージが None なら、 Noneを返す
        assert chat_prompt.get_responder_last_msg() is None
        assert chat_prompt.create_prompt()=="ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: "



    def test_remove_last_responder_message_when_last_responder_message_is_none(self):
        chat_prompt = ChatPromptRinnaForTest()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg(None)

        # responder の最後のメッセージが None なら、 Noneを返す
        assert chat_prompt.get_responder_last_msg() is None
        # 削除前の最後のレスポンダメッセージ
        last_responder_msg_before = chat_prompt.get_responder_last_msg()

        # 最後のレスポンダメッセージを削除
        chat_prompt.remove_last_responder_message()

        # 削除後の最後のレスポンダメッセージ
        last_responder_msg_after = chat_prompt.get_responder_last_msg() if chat_prompt.responder_messages else None

        # 削除前と削除後のレスポンダメッセージが同じであることを確認
        assert last_responder_msg_before == last_responder_msg_after

        # 最後のリクエスタメッセージを確認
        last_requester_msg = chat_prompt.get_requester_last_msg()
        assert last_requester_msg =="渋谷の観光地を教えてください。"


        # 削除したあとでも もとの responder の最後のメッセージが None なら、 Noneを返す
        assert chat_prompt.get_responder_last_msg() is None
        assert chat_prompt.create_prompt()=="ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: "

