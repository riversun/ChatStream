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

            if self.params.get("mock_type") == "round":
                line = sample_text_array[(chat_prompt.get_turn() - 1) % len(
                    sample_text_array)]
            else:
                line = sample_text_long

            tokens = line.split(' ')
            resp_text = ""

            prev = ""
            for index, updated_text in enumerate(tokens):
                if index == 0:
                    resp_text += updated_text
                else:
                    resp_text += " " + updated_text

                updated_text = resp_text[len(prev):]
                pos = "mid"
                if index == 0:
                    pos = "begin"

                await asyncio.sleep(0.1)  # わずかな遅延を発生させ、逐次返信となるようにする

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
            print(f"Client disconnected: {e}")
