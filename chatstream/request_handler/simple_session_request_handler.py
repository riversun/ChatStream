import json
import traceback
import uuid

from fastapi import Request
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse

from .request_handler import AbstractRequestHandler
from ..util_request_id import req_id


class SimpleSessionRequestHandler(AbstractRequestHandler):
    """
    FastAPI/Starlette の Request を処理し、 chat_prompt(会話履歴) を  HTTPセッション に格納するリクエストハンドラ

    リクエストハンドラは chat_prompt をどこに保存するか、によって実装される。
    本リクエストハンドラは chat_prompt をセッションに保存するための実装となる。
    関連して、ブラウザからのアクセス時のロール情報の保持は、 chat_prompt の置き場とは無関係に、
    一時的にセッションに保存される。
    """

    def __init__(self, session_attr_name="session"):
        super().__init__()
        self.session_attr = session_attr_name

    def get_request_handler_type(self):
        return "http_session"

    async def process_request(self, request: Request, request_body, streaming_finished_callback):
        """
        FastAPI/Starlette の Request を処理し、 chat_prompt(会話履歴を含むプロンプト) をオンメモリのセッションに格納する
        chat_prompt をセッションに保存する request_handler

        :param request:
        :param request_body:
        :param streaming_finished_callback: ストリームの送出終了を受け取るコールバック関数
        :return:
        """

        try:

            self.logger.debug(self.eloc.to_str({"en": f"{req_id(request)} Starts handling the request",
                                                "ja": f"{req_id(request)} リクエストのハンドリングを開始します"}))

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

                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Since chat_prompt does not exist in the session, create a new one.",
                     "ja": f"{req_id(request)} chat_prompt がセッションに存在しないので、新規生成します"}))

                chat_prompt = self.chat_prompt_clazz()  # ChatPrompt をインスタンス化する

                chat_prompt.build_initial_prompt(chat_prompt)  # 初期プロンプトを生成する

                # 会話履歴をセッションに保持する
                session["chat_prompt"] = chat_prompt
                session_mgr.save_session()  # .save_session("chat_prompt")

            chat_prompt = session.get("chat_prompt")

            if request_body is not None:
                # request_body が明示的に指定された場合

                self.logger.debug(self.eloc.to_str({
                    "en": f"{req_id(request)} Since request_body is specified, the request data is retrieved from it. The request may have been intercepted by the Web API front-end.",
                    "ja": f"{req_id(request)} request_body が指定されているため、そこからリクエストデータを取得します。リクエストが Web API のフロント処理でインターセプトされた可能性があります。"}))

                # request はストリームで提供されるため、どこかで読み取ると consume されてしまう。
                # そこで、もしどこかでインターセプトしてリクエストされたデータを使いたい場合は
                # インターセプト元で request_body をキャッシュし、再度指定して chatstream を呼び出すことでrequest が consume されていても処理を先に進めることができる
                data = json.loads(request_body)
            else:
                data = await request.json()

            user_input = data.get("user_input", None)  # ユーザーの入力テキスト

            local_reponse = self.detect_special_command_for_role_promotion(request, user_input, streaming_finished_callback)
            if local_reponse is not None:
                return local_reponse

            # 入力オブジェクトから "regenerate" パラメータを取得する。(True/False)
            need_regenerate = self.get_bool_from_dict(data, "regenerate")

            self.logger.debug(self.eloc.to_str(
                {"en": f"{req_id(request)} Get Parameters user_input:{user_input} regenerate:{need_regenerate}",
                 "ja": f"{req_id(request)} パラメータ取得 user_input:{user_input} regenerate:{need_regenerate}"}))

            if need_regenerate:
                # AIアシスタント側の再生成モードのとき

                self.logger.debug(self.eloc.to_str({
                    "en": f"{req_id(request)} Do regenerate. user_input(request_last_msg used at regenerate):'{chat_prompt.get_requester_last_msg()}'",
                    "ja": f"{req_id(request)} regenerate します。 user_input(regenerate時に使用される request_last_msg):'{chat_prompt.get_requester_last_msg()}'"}))

                if chat_prompt.is_empty():
                    # - ユーザー・AIアシスタント(responder)間で、まだ会話が何も存在しない場合
                    # => まだ会話が存在しないときに、 "regenerate" を実行した場合は、
                    # internal server error とする。
                    # 基本的にはフロントエンド側で会話が何も存在しないときにサーバーに投げないように設計しておくのが前提
                    return await self.return_internal_server_error_response(request, streaming_finished_callback,
                                                                            "regenerate requested even though the prompt is empty");

                else:
                    # - ユーザー・AIアシスタント(responder)間で、会話ターンが進行している場合
                    chat_prompt.clear_last_responder_message()  # responder の 最後のメッセージを None にする

            else:
                # 通常の場合(AIアシスタント側の再生成ではない)

                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Add user input data into chat_prompt user_input:'{user_input}'",
                     "ja": f"{req_id(request)} chat_prompt にユーザー入力データを追加 user_input:'{user_input}"}))
                chat_prompt.add_requester_msg(user_input)
                chat_prompt.add_responder_msg(None)

            async def chat_generation_finished_callback(message):
                """
                チャットのストリーミング生成の完了コールバックを処理する
                """
                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Text generation end callback received message:'{message}'",
                     "ja": f"{req_id(request)} 文章生成終了コールバックを受信しました message:'{message}'"}))

                # 生成された文章のストリーミングが終了したときに実行される
                if message == "success":
                    # 生成された文章のストリーミングが正常終了したとき(クライアントからの切断・ネットワーク断が発生していない)
                    # AIによる文章生成が無事終了したと判断できるため、ここでセッション情報を保存する

                    # セッション内容を保存する
                    # セッション全体を保存する、というのが Too Much であることがわかったら、 chat_prompt のみ保存,または差分保存を導入する。
                    session_mgr.save_session()

                    self.logger.debug(
                        self.eloc.to_str({"en": f"{req_id(request)} Saved session content",
                                          "ja": f"{req_id(request)} セッション内容を保存しました"}))
                elif message == "client_disconnected_while_streaming":
                    # クライアントに対して、文章ストリーミングを送出中にネットワークエラーまたは、クライアントから明示的に切断されたとき
                    session_mgr.save_session()

                    self.logger.debug(
                        self.eloc.to_str({
                            "en": f"{req_id(request)} A network error occurred, but the session content was saved halfway through",
                            "ja": f"{req_id(request)} ネットワークエラーが発生しましたが、セッション内容は途中まで保存しました"}))
                    pass
                elif message.startswith("unknown_error_occurred"):
                    # 予期せぬエラー（一般的な Syntax Errorなど)
                    pass
                else:
                    # message=="client_disconnected_before_streaming": はこの上位のキューイングループのみでハンドリングできるので、このコールバックには到達しない
                    pass

                # request 処理が正常終了したことを指定されたコールバック関数に通知.このコールバックは実際は上位の キューイングループ
                await streaming_finished_callback(request, message)

            custom_generation_params = session.get("generation_params", None)
            message_id = str(uuid.uuid4())
            generator = self.generate(chat_prompt, chat_generation_finished_callback, request, custom_generation_params, message_id=message_id)

            streaming_response = StreamingResponse(generator, media_type="text/plain")

            # レスポンスヘッダをセットする
            # レスポンスヘッダに生成した最新メッセージ用の message_id を付与する
            headers = {"X-ChatStream-Last-Generated-Message-Id": message_id}

            for key, value in headers.items():
                streaming_response.headers[key] = value

            self.logger.debug(self.eloc.to_str({
                "en": f"A message ID:'{message_id}' was issued to identify the currently generated sentence, and was added to the response header 'X-ChatStream-Last-Generated-Message-Id'.",
                "ja": f"現在生成中の文章を特定するための メッセージID:'{message_id}' を発行し、レスポンスヘッダ 'X-ChatStream-Last-Generated-Message-Id' に付与しました。"}))

            self.logger.debug(self.eloc.to_str({
                "en": f"{req_id(request)} StreamingResponse is generated from the sequential text generator. This is returned as the return value.",
                "ja": f"{req_id(request)} 逐次文章生成の generator から StreamingResponse 生成しました。これを戻り値として return　します"}))
            return streaming_response

        except Exception as e:
            # ここで、一般的なエラーをキャッチする。
            # 非同期 generator が値を streamresponse で返し始めた後、
            # generator内で exceptionを raise しても、ここでキャッチできないことに注意。
            self.logger.debug(self.eloc.to_str({
                "en": f"{req_id(request)} An unexpected error occurred during request handler execution. {e}\n{traceback.format_exc()}",
                "ja": f"{req_id(request)} リクエストハンドラ実行中に予期せぬエラーが発生しました {e}\n{traceback.format_exc()}"}))

            return await self.return_internal_server_error_response(request, streaming_finished_callback,
                                                                    "simple session request")

    async def return_internal_server_error_response(self, request, callback, detail):
        """
        Internal Server Error の応答を生成する

        本メソッドは、 Internal Server Error を JSON のエラーレスポンスとして返すときに使用する
        逆に各行で return JSONResponse をすることは禁止とする。
        禁止の理由は streaming_finished_callback コールバックの　返し忘れ　を防ぐため。
        もし、返し忘れで streaming_finished_callback　をコールバックしないと、
        同時アクセスキューイングシステムでアクセスブロックに使用しているセマフォが解放されず
        次のリクエストを受け付けられない事態となってしまう。
        """
        await callback(request, f"unknown_error_occurred,while processing {detail}")
        return JSONResponse(
            content={"error": "internal_server_error", "detail": f"{detail}"}, status_code=500,
            media_type="application/json")

    def get_bool_from_dict(self, data: dict, key: str) -> bool:
        """
        辞書 dict オブジェクトから、安全に、指定したキーの bool値 を取得する

        キーが存在しない場合や、値が bool型 でない場合は False を返す。

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
