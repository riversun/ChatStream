from typing import Generator

from .chat_prompt import AbstractChatPrompt
from .chat_core import process_chat
import asyncio

from tokflow import TokFlow

UPDATE_RESPONDER_TOKEN_ONE_BY_ONE = True


class ChatGenerator:
    def __init__(self, model, tokenizer, device, params):  # , chat_mode):
        self.model = model
        self.tokenizer = tokenizer
        self.device = device
        self.params = params

        self.tflow_for_updated_text = None
        self.tflow_for_response_text = None

    async def generate(self, chat_prompt: AbstractChatPrompt, opts: dict = {}) -> Generator:
        """
        chat_prompt として入力された会話履歴データをもとに、 L{process_chat} に文章生成を指示し
        逐次生成された文章から以下3点を
        
        1. 生成済文章全体(response_text)
        2. 新規生成(updated_text)
        3. 現在のトークン位置
        
        データ化し、それをyield する generator としてふるまう。
        
        :param chat_prompt: 会話履歴を含む ChatPrompt オブジェクト
        :param opts: 
            出力タイプ(output_type の指定):
            opts={"output_type":"updated_text"} とすると、新規生成されたトークンのみ yield する。コンソールチャットではこちらが向いている。
            opts={"output_type":"response_text"} とすると、新規されたトークンを結合した文章のみ yield する。ブラウザでの表示やマルチバイトの表示にはこちらが向いている。
            
            output_type が無指定の場合は (response_text,updated_text,pos) のタプルが yieldされる。
                
                pos の意味: 生成されたトークンが文章全体においてどの位置にあるかを表す。これにより文頭、文末の処理を行う
                    pos="begin" ・・・現在の chat_prompt によって生成された最初のトークンである
                    pos="mid" ・・・現在の chat_prompt によって生成された中間のトークンである
                    pos="end" ・・・現在の chat_prompt によって生成された最後のトークンである。つまり文末。
        
        :return: 
        """

        output_replacement = chat_prompt.get_replacement_when_output()  # 出力の置換

        if output_replacement is not None and self.tflow_for_updated_text is None:
            self.tflow_for_updated_text = TokFlow(output_replacement)
            self.tflow_for_response_text = TokFlow(output_replacement)

        prompt = chat_prompt.create_prompt()  # これまでの会話履歴を含んだプロンプトを生成する

        otype = opts.get("output_type", None)
        post_process_callback = opts.get("post_process_callback", None)

        if chat_prompt.is_chat_mode_enabled():
            stop_strs = chat_prompt.get_stop_strs()
        else:
            stop_strs = None

        self.params["stop_strs"] = stop_strs

        # process_chat() は async 関数で、非同期ジェネレータを返す
        # 非同期ジェネレータを使用する場合は async for を用いて結果を順次取得するため、以下呼出しでの await は不要となる。
        async_generator = process_chat(self.model, self.tokenizer, self.device, self.params, prompt)

        prev = ""

        index = 0
        async for response_text in async_generator:  # async な generator は enumerate を使えないので、自前でループまわす

            pos = "mid"
            if index == 0:
                pos = "begin"

            if chat_prompt.is_chat_mode_enabled():

                if UPDATE_RESPONDER_TOKEN_ONE_BY_ONE:
                    # AIが生成したトークンを生成されたタイミングで逐次 chat_prompt の履歴に反映する設定のとき
                    #
                    # "USER:東京の首都は？ AI:それは、東京です" という文章生成タスクの場合
                    # 最終的に yield したい response_text は "それは、東京です" の部分となる。
                    #
                    # そこで、 "USER:東京の首都は？ AI:それは、東京です" から  "それは、東京です"　をスライスするために、
                    #  "USER:東京の首都は？ AI:" の部分の長さを特定する。

                    # ここで、UPDATE_RESPONDER_TOKEN_ONE_BY_ONE=True の場合、
                    # AIが生成したトークンを順次 chat_prompt 会話履歴に反映していくため
                    # chat_prompt.create_prompt すると、
                    # トークンの逐次生成において以下のように逐次履歴が成長する。
                    #
                    # "USER:東京の首都は？ AI:そ"
                    # "USER:東京の首都は？ AI:それ"
                    # "USER:東京の首都は？ AI:それは、"
                    #
                    #
                    # そこで、 "USER:東京の首都は？ AI:" の部分をスライスするために、omit_last_message=True を指定して、
                    # 最後のメッセージ部分(つまり、このターンだと "それは、") を省略したぶんの長さ(skip_len) を取得し、
                    # "USER:東京の首都は？ AI:それは、"　から "USER:東京の首都は？ AI:" をスライスして "それは、" を残して
                    # response_text にセットする
                    #
                    # 他方　UPDATE_RESPONDER_TOKEN_ONE_BY_ONE=False の場合は、
                    # 会話履歴は成長しないので、response_text[chat_prompt.get_skip_len():]が常に
                    # "USER:東京の首都は？ AI" をあらわす。
                    response_text = response_text[chat_prompt.get_skip_len(omit_last_message=True):].strip()
                else:
                    response_text = response_text[chat_prompt.get_skip_len():].strip()
            else:
                # response_text = response_text[len(prompt):].strip()
                pass

            updated_text = response_text[len(prev):]

            updated_text_to_disp = self.tflow_for_updated_text.put(updated_text)
            response_text_to_disp = self.tflow_for_response_text.put(response_text)

            if otype == "updated_text":
                yield updated_text_to_disp
            elif otype == "response_text":
                yield response_text_to_disp
            else:
                yield response_text_to_disp, updated_text_to_disp, pos
            await asyncio.sleep(0.01)  # わずかな遅延を発生させ、逐次返信となるようにする
            prev = response_text

            if UPDATE_RESPONDER_TOKEN_ONE_BY_ONE:
                # 1トークンあらたに生成されるごとに、chat_prompt を更新する
                # この方式のメリットは、途中まで文章生成をしたが、ネットワーク断などで
                # 最後まで生成できなかった場合でも途中の生成したところまでを chat_prompt に履歴を反映しておける点
                chat_prompt.set_responder_last_msg(response_text.strip())

            index += 1

        if chat_prompt.is_chat_mode_enabled():

            if not UPDATE_RESPONDER_TOKEN_ONE_BY_ONE:
                # AI側の最後の返信を会話履歴に追加する
                # この方式の場合は、最後まで（文章生成の正常停止まで）トークンが生成できた場合のみ chat_prompt に履歴を反映する
                # もし途中で切断されたら履歴は残らない
                chat_prompt.set_responder_last_msg(response_text.strip())

        pos = "end"

        # tokflow 内に未出力のバッファが存在する可能性があるため flush する
        updated_text_to_disp = self.tflow_for_updated_text.flush()
        response_text_to_disp = self.tflow_for_response_text.flush()

        # 最終メッセージを出力タイプごとに出しわける
        if otype == "updated_text":
            yield updated_text_to_disp
        elif otype == "response_text":
            yield response_text_to_disp
        else:
            yield updated_text_to_disp, response_text_to_disp, pos

        if post_process_callback is not None:
            # 逐次出力がすべて終了したので、成功をコールバックする
            await post_process_callback("success")
