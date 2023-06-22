import asyncio
import json
import logging
import os
import signal
import sys
import traceback
import urllib.parse
from typing import Generator

from fastapi import Request, Response
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse

from .access_control.client_role_verifier import ClientRoleVerifier
from .access_control.client_role_wrapper import ClientRoleWrapper
from .chat_process import ChatGenerator
from .chat_process_mock import ChatGeneratorMock
from .chat_stream_api_appender import append_apis
from .chat_stream_middleware_appender import append_middlewares
from .easy_locale import EasyLocale
from .merge_dic import merge_dict
from .request_handler.simple_session_request_handler import SimpleSessionRequestHandler
from .resource_usage import get_resource_usage

from .util_ensure_torch_device import ensure_torch_device
from .util_request_id import req_id
from .util_resource_file_response import _send_resource


class ChatStream:
    def __init__(self,
                 name="node:0",  # Name of this ChatStream instance. The name should be recognizable even if it is distributed across multiple instances.
                 model=None,  # Pre-trained language model in HuggingFace style
                 tokenizer=None,  # HuggingFace style tokenizer
                 num_gpus=None,  # Set number of GPUs used for text generation in this ChatStream instance
                 device=None,  # Run on "cpu" / "cuda" / "mps"
                 num_of_concurrent_executions: int = 2,  # The number of concurrent executions for text generation
                 max_queue_size: int = 5,  # The maximum queue size for text generation tasks
                 too_many_request_as_http_error=False,  # True: When 'Too many requests' situation , it returns the status as 429
                 use_mock_response=False,  # True: Returns fixed phrases for testing. As it doesn't need to load the model, it starts up immediately
                 mock_params={type: "round"},  # "round" / "long" - The type of phrases to return when use_mock_response=True
                 chat_prompt_clazz=None,  # Specifies the class that manages the prompts sent to the language model.
                 max_new_tokens=256,  # The maximum size of the newly generated tokens
                 context_len=1024,  # The size of the context (in terms of the number of tokens)
                 temperature=1.0,  # The temperature value for randomness in prediction
                 top_k=50,  # Value of top K for sampling
                 top_p=1.0,  # Value of top P for sampling
                 repetition_penalty=None,  # Penalty for repetition
                 repetition_penalty_method="multiplicative",  # Calculation method for repetition penalty
                 add_special_tokens=None,  # Options for the tokenizer
                 request_handler=SimpleSessionRequestHandler(),  # Request handler. By default, a handler that simply keeps the session is default
                 logger=None,  # logging object
                 locale=None,  # locale for logging
                 client_roles=None,
                 ):

        if client_roles is None:
            client_roles = {
                "user": {
                    "apis": {
                        "allow": ["chat_stream", "clear_context"],
                        "auth_method": "nothing",  # default role
                        "use_session": True,
                    }
                }}

        self.eloc = EasyLocale({"locale": locale})
        self.queue_worker_task = None
        self.name = name
        self.device = ensure_torch_device(device)

        self.num_gpus = num_gpus

        if self.device is not None and self.device.type != 'cuda':  # not supported 'mps' now
            # cpu が選択された場合
            self.num_gpus = 0

        if use_mock_response:
            self.num_gpus = 0

        if logger is None:
            logger = logging.getLogger('chatstream')
            logger.setLevel(logging.NOTSET)
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter('%(asctime)s [%(name)s][%(levelname)s] %(module)s#%(funcName)s  %(message)s'))

            logger.addHandler(handler)

        self.logger = logger

        self.client_roles = client_roles
        self.client_role_wrapper = ClientRoleWrapper(logger=self.logger, eloc=self.eloc, client_roles=client_roles)

        self.request_handler = request_handler
        self.request_handler.logger = logger
        self.request_handler.eloc = self.eloc
        self.request_handler.client_role_wrapper = self.client_role_wrapper

        self.client_role_verifier = ClientRoleVerifier(self)

        chat_params = {
            "temperature": temperature,  # 0.7,  # Temperatureの値
            "max_new_tokens": max_new_tokens,  # 新たに生成する最大トークンサイズ（何トークン分か。)
            "context_len": context_len,  ## コンテクストのサイズ（何トークン分か。)
            "use_top_k_sampling": top_k is not None,  # True: top K サンプリングを有効にする
            "top_k_value": top_k,  # top K サンプリングの値。
            "use_top_p_sampling": top_p is not None,  # True: top P サンプリングを有効にする
            "top_p_value": top_p,  # top P サンプリングの値
            "use_repetition_penalty": repetition_penalty is not None,  # True:繰り返し同じトークンを生成したときのペナルティを有効する
            "repetition_penalty": repetition_penalty,  # ペナルティの値
            "repetition_penalty_method": repetition_penalty_method,  # ペナルティの計算方法
            "add_special_tokens": add_special_tokens,  # トークナイザーの add_special_tokens 設定
        }

        self.too_many_request_as_http_error = too_many_request_as_http_error

        self.chat_prompt_clazz = chat_prompt_clazz

        self.params = chat_params

        # 最大同時処理数を超えないようブロックするための同時処理カウントセマフォ
        self.concurrent_processing_semaphore = asyncio.Semaphore(num_of_concurrent_executions)

        # ユーザー(ブラウザ)からの request を受け付けるリクエストキュー
        # サイズを -1 している理由は run_on_next_queue 側に次に処理にまわされるものを１件入れるため.
        # そのぶんリクエストキューは -1 している
        self.request_queue = asyncio.Queue(maxsize=(max_queue_size - 1))

        # 現在処理している リクエストタスク が最大同時処理数を超えたとき、
        # 次に実行されるリクエストタスクを一時的に配置しておく「次処理キュー」
        # サイズを +1 している理由は 次処理キューは　現在処理中（言語モデルにより文章生成中）のものと、
        # 次に処理にまわされるものの双方格納できるスペースのため
        self.run_on_next_queue = asyncio.Queue(maxsize=(num_of_concurrent_executions + 1))

        # 現在処理中(文章生成中)の リクエストタスク　が配置されている「処理中キュー」
        self.processing_queue = asyncio.Queue(maxsize=num_of_concurrent_executions)

        # コンソールチャット使用時のシングルユーザー用の ChatPrompt
        self.chat_prompt_for_single_user_on_console = None

        if use_mock_response:
            self.chat_generator = ChatGeneratorMock(model=None, tokenizer=None, device=None,
                                                    params=mock_params)
        else:
            self.chat_generator = ChatGenerator(model, tokenizer, device, chat_params)

        # request_handler にパラメータをセット
        request_handler.chat_generator = self.chat_generator
        request_handler.chat_prompt_clazz = self.chat_prompt_clazz

    async def queue_worker(self):
        """
        A worker for concurrently processing requests from clients. It manages the receipt, processing, and completion of requests.
        """

        try:
            while True:
                # request_queue.get()　でクライアントからのリクエストが発生するのを待つ
                # クライアントからのリクエストが発生したとき
                # 即座にそのリクエストタスク（request, this_request_semaphore, future_resultのタプル）はリクエストキュー(request_queue)から取りだされ
                # 次実行キュー(run_on_next_queue) に詰められる
                self.logger.debug(self.eloc.to_str({"en": f"Queue worker started", "ja": f"キューワーカー開始"}))

                request, request_body, callback, this_request_semaphore, future_result = await self.request_queue.get()

                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Retrieve request tasks from the 'request queue'",
                     "ja": f"{req_id(request)} リクエストキュー'からリクエストタスク取り出し"}))

                # 同時処理カウントセマフォ(concurrent_processing_semaphore) がロックされているときに
                # 短時間（１秒以内）に大量リクエストが来た場合、　次実行キュー(run_on_next_queue) に詰める前に
                # リクエストキュー(request_queue) がいっぱいになるため、実際には run_on_next_queue のサイズ -1 の同時リクエストで
                # too_many_request が発生するので注意。

                # 次実行キュー(run_on_next_queue) の必要性
                # リクエストキュー(request_queue) のみだと、 request_queue.get したあと、 connection_semaphore.acquire の間で宙に浮く
                # リクエストタスク（request, this_request_semaphore, resultのタプル）が発生してしまい、現在の待ち行列の大きさが直接的に
                # 把握しづらくなるため、次に実行されるべきリクエストタスクを一時格納するために導入した

                # リクエストが立て込んでいる場合、　基本的に　次実行キュー(run_on_next_queue) のサイズは 1 となる
                # が、同時処理カウントセマフォ(concurrent_processing_semaphore)が取得され
                # 次実行キュー(run_on_next_queue)からリクエストタスクが dequeue されてから、ループが1周まわるまでの短時間 0 になる
                self.run_on_next_queue.put_nowait(
                    (request, request_body, callback, this_request_semaphore, future_result))

                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Add request task to 'next processing queue",
                     "ja": f"{req_id(request)} リクエストタスクを'次処理キュー'に追加"}))

                # 同時処理カウントセマフォ(concurrent_processing_semaphore)を１つ取得
                await self.concurrent_processing_semaphore.acquire()

                request_task = await self.run_on_next_queue.get()  # 次実行キューを dequeue
                self.processing_queue.put_nowait(request_task)  # 処理中キューに enqueue

                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Request task in progress: Execution rights acquired",
                     "ja": f"{req_id(request)} リクエストタスク処理中： 実行権を獲得"}))

                async def request_processing_finished_callback(request, message):
                    self.logger.debug(
                        self.eloc.to_str({"en": f"{req_id(request)} End callback available message:{message}",
                                          "ja": f"{req_id(request)} 終了コールバックあり message:{message}"}))

                    """
                    文章生成ストリームの終了時に呼び出されるコールバック関数
                    ストリーム終了原因
                    ・message=="success" ストリームがクライアントに向け正常に送出された
                    ・message=="client_disconnected_while_streaming" ストリーム送出中にクライアントから切断された
                    ・message=="client_disconnected_before_streaming" ストリーム送出前にクライアントから切断されていた
                    ・message=="unknown_error_occurred" ストリーム送出中に予期せぬエラーが発生した
                    :param message:
                    :return:
                    """

                    # message は現在のところ、これより先には通知しない
                    self.concurrent_processing_semaphore.release()  # 同時処理管理セマフォをリリースする Release the concurrent processing semaphore
                    await self.processing_queue.get()  # 現在の request を、リクエスト処理中キューから取り出す Get the current request from the request processing queue

                    self.logger.debug(
                        self.eloc.to_str({
                            "en": f"{req_id(request)} Request task in progress: End of text generation message:{message}",
                            "ja": f"{req_id(request)} リクエストタスク処理中： 文章生成終了　message:{message}"}))
                    if callback:
                        callback(request, message)
                    # 上の2つ（セマフォと、キュー）を解放したので、次に処理されるべきリクエストタスクが処理(モデルによる文章生成)できるようになる。

                # concurrent_processing_semaphore を取得した request のみ、ここに入れる
                final_response = None
                try:
                    # request を処理する。responseは逐次出力を担当する StreamResponse になっているため、
                    # response を得たあともストリーミングが続いていることを忘れないこと

                    self.logger.debug(
                        self.eloc.to_str({
                            "en": f"{req_id(request)} Request task in progress: Processing is started by the request handler",
                            "ja": f"{req_id(request)} リクエストタスク処理中： リクエストハンドラにより処理開始"}))

                    final_response = await self.request_handler.process_request(
                        request, request_body,
                        streaming_finished_callback=request_processing_finished_callback)

                except ClientDisconnect as e:
                    # ストリーム送出開始時にクライアントから切断されていたとき

                    await request_processing_finished_callback(request, "client_disconnected_before_streaming")
                except Exception as e:
                    #  ストリーム送出開始時に想定していないエラーが発生したとき

                    self.logger.warning(
                        self.eloc.to_str(
                            {"en": f"{req_id(request)} An unexpected error has occurred. {e}\n{traceback.format_exc()}",
                             "ja": f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}"}))

                    final_response = JSONResponse(
                        content={"error": "internal_server_error", "detail": "generating response"}, status_code=500,
                        media_type="application/json")

                    await request_processing_finished_callback(request, "unknown_error_occurred,while process_request")

                finally:
                    # response を 非同期用 result に詰めるが、
                    # response を return してもリクエスト処理がおわるわけではなく、
                    # クライアントへのストリーミングが継続することに留意する必要がある。
                    future_result.set_result(final_response)

                    # リクエストの受付処理が終わったという意味で、セマフォを解放して URLエンドポイント側の処理に返す
                    # 上述のとおり、このタイミングではまだクライアントへストリーミングが継続しているため
                    # ストリーミング完了は callback 関数にて判断すること
                    this_request_semaphore.release()

        except asyncio.CancelledError:
            print("Queue worker stopped.")
        except KeyboardInterrupt:
            print("Interrupted by user, shutting down.")
        except Exception as e:
            # リクエスト処理中に想定していないエラーが発生した場合
            self.logger.warning(
                self.eloc.to_str(
                    {"en": f"{req_id(request)} An unexpected error has occurred. {e}\n{traceback.format_exc()}",
                     "ja": f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}"}))

    async def start_queue_worker(self):
        """
        Starts the queue worker and registers the force termination and shutdown handlers.
        """

        self.queue_worker_task = asyncio.create_task(self.queue_worker())  # キューワーカーを開始

        # 強制終了のシャットダウンハンドラを登録
        signal.signal(signal.SIGINT, lambda s, f: os._exit(0))

    def verify_role_for_api(self, request, api_name):
        """
        指定した API 名のロールをみて、そのAPIにアクセス可能かどうか判定する
        :param request:
        :param api_name:
        :return:
        """
        verify_result = self.client_role_verifier.verify_client_role(request, api_name)
        is_verify_success = verify_result.get("success", False)
        if not is_verify_success:
            return JSONResponse(status_code=403, content={"success": False, "message": "Forbidden", "detail": "Denied on role layer."})
        return None

    async def handle_chat_stream_request(self, request: Request, request_body=None, callback=None):
        """
        This method performs sequential text generation based on user input received, using a pre-trained language model.

        The 'request' should be a FastAPI/Starlette Request object, with an expected JSON format in the request body as {"user_input": userText}.

        The 'response' is a StreamingResponse, which supports streaming text generation on the client side.

        This method automatically handles high traffic load due to simultaneous access by multiple users, without any special handling needed on the Web API implementation side.

        The key features are summarized below:

        1. Text Generation
        Token generation is performed one token at a time, and a streaming response (sequential transmission) is sent to the client. This contributes to a better user experience, as users do not have to wait until the entire text is generated.

        2. Conversation History Retention
        The conversation history between the user and the language model is kept on the server side in memory, by default, through the HTTP session function. The session duration can be configured, but by default, it lasts as long as the browser is open. This allows for a multi-round web chat with a consistent context. Expired sessions are periodically cleaned up from memory. The method for maintaining conversation history can be customized depending on the presence of login functionality (user identification) and the method for session persistence. Specifically, a custom request handler class implementing L{AbstractRequestHandler} can be prepared.

        3. Concurrent Processing and Queuing
        Designed with simultaneous access from multiple clients in mind, it is controlled according to the following parameters specified in the constructor:

        num_of_concurrent_executions: int... Number of simultaneous execution tasks for text generation to the pre-trained language model.
        max_queue_size: int... Size of the queue for text generation tasks. When the number of simultaneous execution tasks falls below the limit.

        Tasks for text generation are transitioned from the top of the waiting queue in order. If a request comes in that exceeds the size of the waiting queue, a 429 too_many_requests response is returned.

        """

        api_name = "chat_stream"
        verify_error_response = self.verify_role_for_api(request, api_name)
        if verify_error_response:
            return verify_error_response

        # この request の処理待ち用カウントセマフォをつくる
        this_request_semaphore = asyncio.Semaphore(0)

        # 非同期操作の結果を保持するための Future オブジェクトをつくる
        future_result = asyncio.Future()

        try:
            # リクエストキュー（処理待ち行列）にリクエストタスク(request, this_request_semaphore, future_result)を追加する
            self.request_queue.put_nowait(
                (request, request_body, callback, this_request_semaphore,
                 future_result))  # put_nowait=>キューが一杯でない場合にのみ要求を追加

            self.logger.debug(self.eloc.to_str(
                {
                    "en": f"{req_id(request)} Add this request to the 'request queue. Queue Size:{self.request_queue.qsize()}/{self.request_queue.maxsize}",
                    "ja": f"{req_id(request)} このリクエストを'リクエストキュー'に追加 キューサイズ:{self.request_queue.qsize()}/{self.request_queue.maxsize}"
                }))

        except asyncio.QueueFull:

            # リクエストキュー（処理ち行列）を超えるリクエストがあった場合はエラーを返す
            # クライアント側ではこのエラーを受け取ったたら、エラーの旨と、再送のボタンなどを表示する

            self.logger.debug(self.eloc.to_str(
                {
                    "en": f"{req_id(request)} Failed to add this request to the 'request queue'. Request queue is full.",
                    "ja": f"{req_id(request)} このリクエストを'リクエストキュー'に追加失敗。リクエストキューがいっぱいです"
                }))

            if self.too_many_request_as_http_error:
                return JSONResponse(content={"error": "too_many_requests"}, status_code=429,
                                    media_type="application/json")
            else:
                return JSONResponse(content={"error": "too_many_requests"}, media_type="application/json")
        except Exception as e:
            # リクエスト処理中に想定していないエラーが発生した場合

            self.logger.warning(
                self.eloc.to_str(
                    {"en": f"{req_id(request)} An unexpected error has occurred. {e}\n{traceback.format_exc()}",
                     "ja": f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}"}))

            return JSONResponse(
                content={"error": "internal_server_error", "detail": "queueing request"}, status_code=500,
                media_type="application/json")

        # この request がリクエスト処理キューで処理されるのをまつ
        await this_request_semaphore.acquire()  # 処理待ち用カウントセマフォが releaseされるのを待つ / Wait for the waiting count semaphore to be released

        self.logger.debug(self.eloc.to_str({"en": f"{req_id(request)} Semaphore for this request has been released.",
                                            "ja": f"{req_id(request)} このリクエスト用セマフォは解放されました"}))

        return await future_result

    async def handle_get_resource_usage_request(self, request: Request):
        try:
            api_name = "get_resource_usage"
            verify_error_response = self.verify_role_for_api(request, api_name)
            if verify_error_response:
                return verify_error_response

            memory_usage = get_resource_usage({"num_gpus": self.num_gpus, "device": self.device})

            memory_usage["name"] = self.name

            return {"success": True, "message": "success", "memory_usage": [memory_usage]}


        except Exception as e:
            tb = traceback.format_exc()
            sys.stderr.write(tb)
            self.logger.warning(
                self.eloc.to_str(
                    {"en": f"{req_id(request)} An unexpected error has occurred. {e}\n{traceback.format_exc()}",
                     "ja": f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}"}))

            return {"success": False, "message": "Error occurred"}

    async def handle_clear_context_request(self, request: Request, request_body=None, callback=None):
        """
        コンテクストをクリアする
        :param request:
        :param request_body:
        :param callback:
        :return:
        """
        try:
            api_name = "clear_context"

            verify_error_response = self.verify_role_for_api(request, api_name)
            if verify_error_response:
                return verify_error_response

            session_mgr = getattr(request.state, "session", None)

            if session_mgr:
                # セッションオブジェクト（辞書オブジェクト）を取得する
                session = session_mgr.get_session()
                chat_prompt = session.get("chat_prompt")

                if chat_prompt:
                    session.pop("chat_prompt", None)  # 削除する

                self.logger.debug(self.eloc.to_str({"en": f"{req_id(request)} Context has been cleared.",
                                                    "ja": f"{req_id(request)} コンテクストがクリアされました"}))

                return {"success": True, "message": "Context successfully cleared"}
            else:
                self.logger.debug(
                    self.eloc.to_str({"en": f"{req_id(request)} Attempted to clear context, but session did not exist",
                                      "ja": f"{req_id(request)} コンテクストをクリアしようとしましたが、セッションは存在しませんでした"}))

                return {"success": False, "message": "no context."}

        except Exception as e:
            tb = traceback.format_exc()
            sys.stderr.write(tb)
            self.logger.warning(
                self.eloc.to_str(
                    {"en": f"{req_id(request)} An unexpected error has occurred. {e}\n{traceback.format_exc()}",
                     "ja": f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}"}))

            return {"success": False, "message": "Error occurred"}

    async def handle_set_generation_params_request(self, request: Request):
        """
        文章生成パラメータ（temperature, top_k_value, top_p_value）の設定を更新する Web API エンドポイントのハンドリングをする

        :param request: クライアントからのリクエスト。次のキーを含む JSON 形式を想定
                        temperature (0.0 から 1.0 の範囲), top_k_value (1 から 500 の範囲), top_p_value (0.0 から 1.0 の範囲).
        :type request: Request
        :return: 処理結果の辞書。
        成功時には "success": True 、失敗時には "success": False
                 "generation_params" は、クライアントによって指定された有効な生成パラメータ
        :rtype: dict

        指定された生成パラメータが適切な範囲にあるかを確認し適切な範囲から外れている場合、エラーメッセージを含む応答が返される
        """

        try:
            api_name = "set_generation_params"
            verify_error_response = self.verify_role_for_api(request, api_name)
            if verify_error_response:
                return verify_error_response

            generation_params_from_client = await request.json()

            temperature = generation_params_from_client.get("temperature")
            top_k_value = generation_params_from_client.get("top_k_value")
            top_p_value = generation_params_from_client.get("top_p_value")

            user_specified_generation_params = {
                "temperature": temperature,
                "top_k_value": top_k_value,
                "top_p_value": top_p_value
            }

            if temperature is not None and not (0.0 <= temperature <= 1.0):
                error_message = "Invalid temperature value. Temperature should be between 0.0 and 1.0."
                return {"success": False, "message": error_message}

            if top_k_value is not None and not (1 <= top_k_value <= 500):
                error_message = "Invalid top_k value. top_k_value should be between 1 and 500."
                return {"success": False, "message": error_message}

            if top_p_value is not None and not (0.0 <= top_p_value <= 1.0):
                error_message = "Invalid top_p value. top_p_value should be between 0.0 and 1.0."
                return {"success": False, "message": error_message}

            session_mgr = getattr(request.state, "session", None)

            if session_mgr:
                # セッションオブジェクト（辞書オブジェクト）を取得する
                session = session_mgr.get_session()

                # ユーザーが設定した生成パラメータをセッションに保存
                session["generation_params"] = user_specified_generation_params;

                # デフォルト(ChatStream初期化時に指定された)の生成パラメータ
                crr_params = {
                    "temperature": self.params.get("temperature"),
                    "top_k_value": self.params.get("top_k_value"),
                    "top_p_value": self.params.get("top_p_value"),
                }

                merged_params = merge_dict(crr_params, user_specified_generation_params)

                return {
                    "success": True, "message": "success",
                    "generation_params": merged_params
                }
            else:
                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Attempted to update generation parameters, but session did not exist",
                     "ja": f"{req_id(request)} 生成パラメータを更新しようとしましたが、セッションは存在しませんでした"}))

                return {"success": False, "message": "no session", "generation_params": None}

        except Exception as e:
            tb = traceback.format_exc()
            sys.stderr.write(tb)
            self.logger.warning(
                self.eloc.to_str(
                    {"en": f"{req_id(request)} An unexpected error has occurred. {e}\n{traceback.format_exc()}",
                     "ja": f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}"}))

            return {"success": False, "message": "error occurred"}

    async def handle_get_generation_params_request(self, request: Request):
        try:
            api_name = "get_generation_params"
            verify_error_response = self.verify_role_for_api(request, api_name)
            if verify_error_response:
                return verify_error_response

            session_mgr = getattr(request.state, "session", None)

            if session_mgr:
                # セッションオブジェクト（辞書オブジェクト）を取得する
                session = session_mgr.get_session()

                # ユーザーが指定した生成パラメータをセッションに保存
                session_stored_generation_params = session.get("generation_params", {});

                # デフォルトの生成パラメータ
                crr_params = {
                    "temperature": self.params.get("temperature"),
                    "top_k_value": self.params.get("top_k_value"),
                    "top_p_value": self.params.get("top_p_value"),
                }
                # ChatStream 初期化時に指定された生成パラメータに、現在セッションで保持されているユーザーごとの生成パラメータをマージしたものを返す
                merged_params = merge_dict(crr_params, session_stored_generation_params)

                return {
                    "success": True, "message": "success",
                    "generation_params": merged_params
                }
            else:

                self.logger.debug(self.eloc.to_str(
                    {"en": f"{req_id(request)} Attempted to retrieve generation parameters, but session did not exist",
                     "ja": f"{req_id(request)} 生成パラメータを取得しようとしましたが、セッションは存在しませんでした"}))

                return {"success": False, "message": "no session", "generation_params": None}

        except Exception as e:
            tb = traceback.format_exc()
            sys.stderr.write(tb)
            self.logger.warning(self.eloc.to_str({
                "en": f"{req_id(request)} An unexpected error occurred while trying to retrieve the generation parameters　{e}\n{traceback.format_exc()}",
                "ja": f"{req_id(request)} 生成パラメータを取得しようとしたところ予期せぬエラーが発生しました　{e}\n{traceback.format_exc()}"}))

            return {"success": False, "message": "error occurred"}

    async def handle_get_prompt_request(self, request: Request):
        try:

            api_name = "get_prompt"
            verify_error_response = self.verify_role_for_api(request, api_name)
            if verify_error_response:
                return verify_error_response

            session_mgr = getattr(request.state, "session", None)
            if session_mgr:
                # セッションオブジェクト（辞書オブジェクト）を取得する
                session = session_mgr.get_session()
                chat_prompt = session.get("chat_prompt")
                if chat_prompt is None:
                    self.logger.debug(
                        self.eloc.to_str({"en": f"{req_id(request)} Attempted to get prompt, but prompt is not yet set",
                                          "ja": f"{req_id(request)} プロンプトを取得しようとしましたが、プロンプトはまだセットされていません"}))

                    return {"success": True, "message": "no prompt", "prompt": None}

                str_prompt = chat_prompt.create_prompt()
                str_prompt_encoded = urllib.parse.quote(str_prompt)

                return {"success": True, "message": "success", "prompt": str_prompt_encoded}
            else:

                self.logger.debug(self.eloc.to_str({"en": f"{req_id(request)} Got prompt, but session did not exist",
                                                    "ja": f"{req_id(request)} プロンプトを取得しましたが、セッションは存在しませんでした"}))

                return {"success": False, "message": "no context.", "prompt": None}

        except Exception as e:
            tb = traceback.format_exc()
            sys.stderr.write(tb)

            self.logger.warning(self.eloc.to_str({
                "en": f"{req_id(request)} An unexpected error occurred while attempting to retrieve the context　{e}\n{traceback.format_exc()}",
                "ja": f"{req_id(request)} コンテクストを取得しようとしたところ予期せぬエラーが発生しました　{e}\n{traceback.format_exc()}"}))

            return {"success": False, "message": "error occurred"}

    async def handle_get_load_request(self, request: Request):
        """
        Return information about the current processing state (waiting state)
        """
        api_name = "get_load"
        verify_error_response = self.verify_role_for_api(request, api_name)
        if verify_error_response:
            return verify_error_response

        return {
            "success": True,
            "message": "success",
            "chatstream_workers": [
                {
                    "name": self.name,
                    "processing": self.processing_queue.qsize(),
                    "waiting": self.run_on_next_queue.qsize() + self.request_queue.qsize(),
                    "_num_of_next_queue": self.run_on_next_queue.qsize(),
                    "_num_of_request_queue": self.request_queue.qsize(),
                    "max_processing": self.processing_queue.maxsize,
                    "max_waiting": self.request_queue.maxsize + self.run_on_next_queue.maxsize
                },
            ],
        }

    async def index(self, request: Request, response: Response, opts={}):

        api_name = "webui_index"
        verify_error_response = self.verify_role_for_api(request, api_name)
        if verify_error_response:
            return verify_error_response

        ui_init_params = opts.get("ui_init_params", None)

        if ui_init_params:
            def replacer(text):
                return text.replace("const opts = {}", f"const opts = {json.dumps(ui_init_params)}")

            return _send_resource(file_name="index.html", replacer=replacer, response=response)
        else:
            return _send_resource(file_name="index.html", response=response)

    async def js(self, request: Request, response: Response):

        api_name = "web_ui_js"
        verify_error_response = self.verify_role_for_api(request, api_name)
        if verify_error_response:
            return verify_error_response

        return _send_resource(file_name="chatstream.js", response=response)

    async def handle_console_input(self, user_input: str) -> Generator:
        """
        コンソールチャット向けのクライアントからの入力を処理し、対応するレスポンスを生成する
        本メソッドはモデル入出力と挙動のカジュアルな確認用に用いることができる

        :param user_input: ユーザーからの入力。この入力に基づいて事前学習済モデルがレスポンスを生成する
        :rtype: Generator
        """
        if self.chat_prompt_for_single_user_on_console is None:
            self.chat_prompt_for_single_user_on_console = self.chat_prompt_clazz()

        self.chat_prompt_for_single_user_on_console.add_requester_msg(user_input)
        self.chat_prompt_for_single_user_on_console.add_responder_msg(None)
        self.chat_generator.generate(self.chat_prompt_for_single_user_on_console)

        async for response_text, updated_text, pos in self.chat_generator.generate(
                self.chat_prompt_for_single_user_on_console):
            yield response_text, updated_text, pos

    def append_apis(self, app, opts={}):
        """
        ChatStreamに関連するWeb APIをFastAPIアプリに追加する。

        chat_stream、app、optsを元に、特定のAPIを追加する。各APIは、そのキーが'include'リストに含まれている、
        'exclude'リストに含まれていない、または'all'がTrueに設定されている場合に有効/無効を切り替えることができる。

        :param chat_stream: APIリクエストを処理するChatStreamオブジェクト。
        :param app: ルートを追加するFastAPIアプリケーション。
        :param dict opts: 追加するAPIを決定するためのオプションの辞書。キーとその意味は次の通り：
            "include": 明示的に含めるAPI名のリスト。
            "exclude": 明示的に除外するAPI名のリスト。
            "all": すべてのAPIを含めるかどうかを決定するブール値。デフォルトはFalse。

        有効にするAPI名リスト（'include'または'exclude'に入れる）:
            "get_prompt": 有効にすると、現在のプロンプトを取得するAPIが追加される。
            "chat_stream": 有効にすると、チャットストリームリクエストを処理するAPIが追加される。
            "clear_context": 有効にすると、コンテキストをクリアするAPIが追加される。
            "get_load": 有効にすると、チャットストリームの現在の負荷を取得するAPIが追加される。
            "set_generation_params": 有効にすると、チャットストリームの生成パラメータを設定するAPIが追加される。
            "get_resource_usage": 有効にすると、CPUおよびGPUのリソース使用量（メモリ使用量）を取得するAPIが追加される。


        例：
        append_apis(app, {"include": [ "exclude": ["clear_context"]})
        'clear_context' APIは自動追加しない（手動追加は可能)
        """
        append_apis(self, app, opts, logger=self.logger, eloc=self.eloc)

    def append_middlewares(self, app, opts=None):
        """
        ChatStream に関連する ミドルウェア を FastAPI アプリに追加する。
        :param app:
        :param opts:
        :return:
        """
        append_middlewares(self, app, opts=opts, logger=self.logger, eloc=self.eloc)
