import asyncio

from .mock_response_example_text import sample_text_array, sample_text_long


class ChatGeneratorMock:
    """
    動作確認用に、固定的な応答を返す ChatGenerator
    """

    def __init__(self, model, tokenizer, device, params):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.params = params

    async def generate(self, chat_prompt, opts={}):
        try:

            otype = opts.get("output_type", None)
            post_process_callback = opts.get("post_process_callback", None)

            if chat_prompt.is_chat_mode_enabled():
                stop_strs = chat_prompt.get_stop_strs()
            else:
                stop_strs = None

            self.params["stop_strs"] = stop_strs

            time_per_token_sec = self.params.get("time_per_token_sec", 0.1)
            initial_wait_sec = self.params.get("initial_wait_sec", 0)


            if self.params.get("type") == "round":
                line = sample_text_array[(chat_prompt.get_turn() - 1) % len(
                    sample_text_array)]
            elif self.params.get("type") == "echo":
                # ユーザーの最新の入力文をエコーする
                line = chat_prompt.get_requester_last_msg()
            else:
                line = sample_text_long

            tokens,separator =self.split_text(line)
            resp_text = ""

            prev = ""
            for index, updated_text in enumerate(tokens):
                if index == 0:
                    resp_text += updated_text
                    if initial_wait_sec>0:
                        await asyncio.sleep(initial_wait_sec)
                else:
                    resp_text += separator + updated_text

                updated_text = resp_text[len(prev):]
                pos = "mid"
                if index == 0:
                    pos = "begin"

                await asyncio.sleep(time_per_token_sec)  # わずかな遅延を発生させ、逐次返信となるようにする

                # 出力タイプごとに出しわける
                if otype == "updated_text":
                    yield updated_text
                elif otype == "response_text":
                    yield resp_text
                else:
                    yield resp_text, updated_text, pos

                prev = resp_text

            if chat_prompt.is_chat_mode_enabled():
                # AI側の最後の返信を会話履歴に追加する
                chat_prompt.set_responder_last_msg(resp_text.strip())

            pos = "end"

            # 最終メッセージを出力タイプごとに出しわける
            if otype == "updated_text":
                yield ""
            elif otype == "response_text":
                yield ""
            else:
                yield "", "", pos

            if post_process_callback is not None:
                await post_process_callback("success")  # Call the callback function after the generator has finished

        except Exception as e:
            #print(f"Client disconnected: {e}")
            raise e;

    def count_wide_chars(self,s):
        # 全角文字の数をカウントする関数。全角文字の範囲である「！」から「～」、または「　」から「＠」までの文字をカウントする。
        return sum([1 for c in s if ord('！') <= ord(c) <= ord('～') or ord('　') <= ord(c) <= ord('＠')])

    def split_text(self,line):
        """
        英文、２バイト系文（日本語など）を判定し、英文の場合は " " スペース区切り、日本語の場合は、１文字ずつトークナイズ
        """
        # 全角文字の数をカウントする
        wide_char_count = self.count_wide_chars(line)
        # 半角スペースの数をカウントする
        space_count = line.count(' ')

        # 全角文字が3文字以上含まれていて、かつ、半角スペースの数が全角文字の数より少ない場合
        if wide_char_count >= 3 and space_count < wide_char_count:
            # そのテキストを日本語とみなし、1文字ずつに分割する
            tokens = list(line)
            return tokens, ""
        else:
            # そうでない場合、そのテキストを英語とみなし、半角スペースで分割する
            tokens = line.split(' ')
            return tokens, " "


