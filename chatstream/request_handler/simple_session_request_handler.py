from fastapi import Request
from fastapi.responses import StreamingResponse

from .request_handler import AbstractRequestHandler

from ..util_request_id import req_id


class SimpleSessionRequestHandler(AbstractRequestHandler):
    def __init__(self, session_attr_name="session"):
        super().__init__()  # Call the initialization of the base class
        self.session_attr = session_attr_name

    async def process_request(self, request: Request, streaming_finished_callback):
        """
        FastAPI/Starlette の Request を処理し、 chat_prompt(会話履歴を含むプロンプト) をオンメモリのセッションに格納する
        chat_prompt をセッションに保存する request_handler


        """

        self.logger.debug(f"{req_id(request)} リクエストのハンドリングを開始します")

        if not hasattr(request.state, self.session_attr):
            # セッションミドルウェアが存在しない場合はエラー
            raise Exception(
                "Session is not available. Please install 'fastsession' with the command 'pip install fastsession' and add 'FastSessionMiddleware' to the middleware in order to enable sessions and facilitate multi-round chat with conversation history preservation.")

        # セッションマネージャを取得する
        session_mgr = getattr(request.state, self.session_attr, None)

        # セッションオブジェクト（辞書オブジェクト）を取得する
        session = session_mgr.get_session()

        if session.get("chat_prompt") is None:
            # chat_prompt がまだセッションに格納されていない場合
            self.logger.debug(f"{req_id(request)} chat_prompt がセッションに存在しないので、新規生成します")

            chat_prompt = self.chat_prompt_clazz()
            # 会話履歴をセッションに保持する
            session["chat_prompt"] = chat_prompt

        chat_prompt = session.get("chat_prompt")

        data = await request.json()

        user_input = data["user_input"]

        self.logger.debug(f"{req_id(request)} chat_prompt にユーザー入力データを追加 user_input:'{user_input}'")

        chat_prompt.add_requester_msg(user_input)
        chat_prompt.add_responder_msg(None)

        async def chat_generation_finished_callback(message):
            self.logger.debug(f"{req_id(request)} 文章生成終了コールバックを受信しました message:'{message}'")
            # 生成された文章のストリーミングが終了したときに実行される
            if message == "success":
                # 生成された文章のストリーミングが正常終了したとき(クライアントからの切断・ネットワーク断が発生していない)
                # AIによる文章生成が無事終了したと判断できるため、ここでセッション情報を保存する
                # TODO 文章生成が終了したタイミングでセッション全体をストアに保存しているので、
                session_mgr.save_session()  # セッション全体を保存しているので、詳細な差分だけ保存したいような場合は TODO
                self.logger.debug(f"{req_id(request)} セッション内容を保存しました")
            elif message == "client_disconnected_1":
                # クライアントに対して、文章ストリーミングを送出中に
                # ネットワークエラーまたは、クライアントから明示的に切断された
                session_mgr.save_session()  # セッション全体を保存しているので、詳細な差分だけ保存したいような場合は TODO
                self.logger.debug(f"{req_id(request)} ネットワークエラーが発生しましたが、セッション内容は途中まで保存しました")
                pass
            elif message.startsWith("unknown_error_occurred"):
                # 予期せぬエラー（一般的な Syntax Errorなど)
                pass

            # message=="client_disconnected_2": はこの上位のキューイングループのみでハンドリングできるので、ここでは処理できない

            # request 処理が正常終了したことを指定されたコールバック関数に通知
            # このコールバックは実際は上位の キューイングループ
            await streaming_finished_callback(request, message)

        generator = self.generate(chat_prompt, chat_generation_finished_callback)

        streaming_response = StreamingResponse(generator, media_type="text/plain")

        self.logger.debug(
            f"{req_id(request)} 逐次文章生成の generator から StreamingResponse 生成しました。これを戻り値として return　します")
        return streaming_response
