import pytest

# from chatstream import AbstractChatPrompt

from chatstream import ChatPromptRinnaJapaneseGPTNeoxInst as ChatPrompt


# class ChatPromptRinnaForTest(AbstractChatPrompt):
#
#     def __init__(self):
#         super().__init__()  # Call the initialization of the base class
#         self.set_requester("ユーザー")
#         self.set_responder("システム")
#
#     def get_stop_strs(self):
#         if not self.chat_mode:
#             return None
#         return []
#
#     def get_replacement_when_input(self):
#         return [("\n", "<NL>")]
#
#     def get_replacement_when_output(self):
#         return [("<NL>", "\n")]
#
#     def create_prompt(self, omit_last_message=False):
#         if self.chat_mode == False:
#             return self.get_requester_last_msg()
#
#         # Chat Mode == True の場合のプロンプトを構築する
#         ret = self.system;
#         for i, chat_content in enumerate(self.chat_contents):
#             chat_content_role = chat_content.get_role()
#             chat_content_message = chat_content.get_message()
#
#             if omit_last_message and (i == len(self.chat_contents) - 1):
#                 # omit_last_messageが有効で、今が最後のメッセージの場合
#                 chat_content_message = None  # 最後のメッセージパートは無効にする
#
#             if chat_content_role:
#
#                 if chat_content_message:
#                     merged_message = chat_content_role + ": " + chat_content_message + "<NL>"
#                 else:
#                     merged_message = chat_content_role + ": "
#
#                 ret += merged_message
#
#         return ret
#

class TestChatPromptRinna:

    @pytest.fixture
    def chat_prompt(self):
        chat_prompt = ChatPrompt()
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
        chat_prompt = ChatPrompt()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg("渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂")

        assert chat_prompt.get_requester_last_msg() == "渋谷の観光地を教えてください。"
        assert chat_prompt.get_responder_last_msg() == "渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂"

        assert chat_prompt.create_prompt() == "ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: 渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂<NL>"

    def test_remove_last_responder_message(self):
        chat_prompt = ChatPrompt()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg("渋谷の観光地は以下が有名です<NL>ハチ公前<NL>109<NL>道玄坂")

        # 削除前の最後のメッセージを取得
        last_msg_before = chat_prompt.get_responder_last_msg()

        # 最後のメッセージを削除
        chat_prompt.clear_last_responder_message()

        # 削除後の最後のメッセージを取得
        last_msg_after = chat_prompt.get_responder_last_msg() if chat_prompt.responder_messages else None

        # 削除前の最後のメッセージと削除後の最後のメッセージが違うことを確認
        assert last_msg_before != last_msg_after
        # 削除後の最後のメッセージが、削除前のものと違うか、あるいは応答者のメッセージがない場合はNoneであることを確認
        assert last_msg_after == (
            chat_prompt.responder_messages[-1].get_message() if chat_prompt.responder_messages else None)

        # 最後のメッセージを削除しようとする（リクエスターメッセージなので削除されないはず）
        chat_prompt.clear_last_responder_message()

        # 最後のリクエスタメッセージを確認
        last_requester_msg = chat_prompt.get_requester_last_msg()
        assert last_requester_msg == "渋谷の観光地を教えてください。"

        # 削除したあとでも もとの responder の最後のメッセージが None なら、 Noneを返す
        assert chat_prompt.get_responder_last_msg() is None
        assert chat_prompt.create_prompt() == "ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: "

    def test_clear_last_responder_message_when_last_responder_message_is_none(self):
        chat_prompt = ChatPrompt()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg(None)

        # responder の最後のメッセージが None なら、 Noneを返す
        assert chat_prompt.get_responder_last_msg() is None
        # 削除前の最後のレスポンダメッセージ
        last_responder_msg_before = chat_prompt.get_responder_last_msg()

        # 最後のレスポンダメッセージを削除
        chat_prompt.clear_last_responder_message()

        # 削除後の最後のレスポンダメッセージ
        last_responder_msg_after = chat_prompt.get_responder_last_msg() if chat_prompt.responder_messages else None

        # 削除前と削除後のレスポンダメッセージが同じであることを確認
        assert last_responder_msg_before == last_responder_msg_after

        # 最後のリクエスタメッセージを確認
        last_requester_msg = chat_prompt.get_requester_last_msg()
        assert last_requester_msg == "渋谷の観光地を教えてください。"

        # 削除したあとでも もとの responder の最後のメッセージが None なら、 Noneを返す
        assert chat_prompt.get_responder_last_msg() is None
        assert chat_prompt.create_prompt() == "ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: "

    def test_clear_last_responder_message_when_no_messages(self):
        chat_prompt = ChatPrompt()

        # まだメッセージが追加されていないので、responder_messagesが空であることを確認
        assert not chat_prompt.responder_messages

        # 最後のレスポンダメッセージを削除を試みる
        try:
            chat_prompt.clear_last_responder_message()
        except IndexError:
            pytest.fail("remove_last_responder_message threw IndexError when it shouldn't")

        # メッセージがまだないので、レスポンダの最後のメッセージはNoneであることを確認
        assert chat_prompt.get_responder_last_msg() is None

        # メッセージがまだないので、プロンプトはシステムの初期メッセージであることを確認
        assert chat_prompt.create_prompt() == chat_prompt.system

    def test_remove_last_requester_message(self):
        """
        remove_last_requester_messageメソッドの単体テスト
        リクエスターのメッセージリストから最後のメッセージが削除されることを確認
        """
        chat_prompt = ChatPrompt()
        chat_prompt.add_requester_msg("メッセージ1")
        chat_prompt.add_requester_msg("メッセージ2")
        chat_prompt.remove_last_requester_msg()

        assert len(chat_prompt.requester_messages) == 1
        assert chat_prompt.requester_messages[-1].get_message() == "メッセージ1"

    def test_remove_last_responder_message(self):
        """
        remove_last_responder_messageメソッドの単体テスト
        レスポンダーのメッセージリストから最後のメッセージが削除されることを確認
        """
        chat_prompt = ChatPrompt()
        chat_prompt.add_responder_msg("メッセージ1")
        chat_prompt.add_responder_msg("メッセージ2")
        chat_prompt.remove_last_responder_msg()

        assert len(chat_prompt.responder_messages) == 1
        assert chat_prompt.responder_messages[-1].get_message() == "メッセージ1"

    def test_is_empty(self):
        """
        is_empty メソッドの単体テスト
        チャットプロンプトが空のときに True、そうでないときに False を返すことを確認する
        """
        chat_prompt = ChatPrompt()

        # 何もメッセージが追加されていないので、is_empty は True を返すべき
        assert chat_prompt.is_empty() is True

        # リクエスターメッセージを追加
        chat_prompt.add_requester_msg("こんにちは")
        # メッセージが追加されたので、is_empty は False を返すべき
        assert chat_prompt.is_empty() is False

        # リクエスターメッセージを削除
        chat_prompt.remove_last_requester_msg()  # メソッドの実装によりますが、このメソッドが存在しない場合、この行は削除してください
        # すべてのメッセージが削除されたので、is_empty は再び True を返すべき
        assert chat_prompt.is_empty() is True

        # レスポンダーメッセージを追加
        chat_prompt.add_responder_msg("こんにちは")
        # メッセージが追加されたので、is_empty は False を返すべき
        assert chat_prompt.is_empty() is False

    def test_create_prompt_with_omit_last_message(self):
        """
        omit_last_message = True のとき、最後のメッセージ（ロール部分はあり）が空になること
        """
        chat_prompt = ChatPrompt()
        chat_prompt.add_requester_msg("日本のおすすめの観光地を教えてください。")
        chat_prompt.add_responder_msg("どの地域の観光地が知りたいですか？")
        chat_prompt.add_requester_msg("渋谷の観光地を教えてください。")
        chat_prompt.add_responder_msg("ハチ公前がおすすめです。")
        prompt = chat_prompt.create_prompt()
        assert prompt == "ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: ハチ公前がおすすめです。<NL>"
        # print(f"prompt:{prompt}")
        prompt = chat_prompt.create_prompt({"omit_last_message": True})
        assert prompt == "ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: "
        # print(f"prompt:{prompt}")
