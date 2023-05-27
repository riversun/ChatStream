import json

from fastapi import Request
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse

from .request_handler import AbstractRequestHandler

from ..util_request_id import req_id
import traceback


class SimpleSessionRequestHandler(AbstractRequestHandler):
    def __init__(self, session_attr_name="session"):
        super().__init__()  # Call the initialization of the base class
        self.session_attr = session_attr_name

    async def process_request(self, request: Request, request_body, streaming_finished_callback):
        """
        FastAPI/Starlette の Request を処理し、 chat_prompt(会話履歴を含むプロンプト) をオンメモリのセッションに格納する
        chat_prompt をセッションに保存する request_handler
        """
        try:
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

            if request_body is not None:
                # request_body が明示的に指定された場合
                # request はストリームで提供されるため、どこかで読み取ると consume されてしまう。
                # そこで、もしどこかでインターセプトしてリクエストされたデータを使いたい場合は
                # インターセプト元で request_body をキャッシュし、再度指定して chatstream を呼び出すことで
                # request が consume されていても処理を先に進めることができる
                self.logger.debug(
                    f"{req_id(request)} request_body が指定されているため、そこからリクエストデータを取得します。リクエストが Web API のフロント処理でインターセプトされた可能性があります。")
                data = json.loads(request_body)
            else:
                data = await request.json()

            user_input = data.get("user_input", None)

            # 安全に need_regenerate(bool値)を json 由来の data オブジェクトから取得する

            need_regenerate = self.get_bool_from_dict(data, "regenerate")

            self.logger.debug(
                f"{req_id(request)} パラメータ取得 user_input:{user_input} regenerate:{need_regenerate}")

            if need_regenerate:
                self.logger.debug(
                    f"{req_id(request)} regenerate します。 user_input(regenerate時に使用される request_last_msg):'{chat_prompt.get_requester_last_msg()}'")

                if chat_prompt.is_empty():
                    # まだ会話が何も存在しない場合
                    return await self.return_internal_server_error_response(request, streaming_finished_callback,
                                                                            "regenerate requested even though the prompt is empty");

                else:
                    chat_prompt.clear_last_responder_message()  # responder の 最後のメッセージを削除する

            else:
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
                elif message.startswith("unknown_error_occurred"):
                    # 予期せぬエラー（一般的な Syntax Errorなど)
                    pass

                # message=="client_disconnected_2": はこの上位のキューイングループのみでハンドリングできるので、ここでは処理できない

                # request 処理が正常終了したことを指定されたコールバック関数に通知
                # このコールバックは実際は上位の キューイングループ

                self.logger.debug(f"{req_id(request)} 上位にコールバックします")
                await streaming_finished_callback(request, message)

            generator = self.generate(chat_prompt, chat_generation_finished_callback, request)

            streaming_response = StreamingResponse(generator, media_type="text/plain")

            self.logger.debug(
                f"{req_id(request)} 逐次文章生成の generator から StreamingResponse 生成しました。これを戻り値として return　します")
            return streaming_response

        except Exception as e:
            # ここで、一般的なエラーをキャッチするが 非同期 generator が値をstreamresponse で返し始めた後、generator内で exceptionを
            # raise しても、ここでキャッチできないことに注意。
            self.logger.debug(
                f"{req_id(request)} リクエストハンドラ実行中に不明なエラーが発生しました。{e}\n{traceback.format_exc()}")

            return await self.return_internal_server_error_response(request, streaming_finished_callback,
                                                                    "simple session request");

    async def return_internal_server_error_response(self, request, callback, detail):
        """
        Internal Server Error を JSON のエラーレスポンスとして返すときに使用する
        各行で return JSONResponse をすることは禁止
        理由は streaming_finished_callback　コールバックの戻し忘れを防ぐため。
        streaming_finished_callback　をコールバックしないと、
        同時アクセスキューイングシステムでアクセスブロックに使用しているセマフォが解放されず
        次のリクエストを受け付けられない事態となってしまうため。
        """
        await callback(request, f"unknown_error_occurred,while processing {detail}")
        return JSONResponse(
            content={"error": "internal_server_error", "detail": f"{detail}"}, status_code=500,
            media_type="application/json")

    def get_bool_from_dict(self, data: dict, key: str) -> bool:
        """
        安全に辞書からbool値を取得する

        辞書の指定されたキーからbool値を取得。キーが存在しない場合や、値がboolでない場合はFalseを返す。

        Args:
            data (dict): bool値を取得したい辞書
            key (str): 取得したい値のキー

        Returns:
            bool: 辞書から取得したbool値。指定されたキーの値がboolでない場合はFalse
        """
        try:
            value = data[key]
            if isinstance(value, bool):
                return value
        except (KeyError, TypeError):
            pass
        return False
