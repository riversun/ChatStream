import asyncio
import logging
import os
import signal
import traceback
from typing import Generator

from fastapi import Request
from starlette.requests import ClientDisconnect
from starlette.responses import JSONResponse

from .chat_process import ChatGenerator
from .chat_process_mock import ChatGeneratorMock
from .request_handler.simple_session_request_handler import SimpleSessionRequestHandler
from .util_request_id import set_req_id, req_id


class ChatStream:
    def __init__(self,
                 model=None,  # Pre-trained language model in HuggingFace style
                 tokenizer=None,  # HuggingFace style tokenizer
                 device=None,  # Run on "cpu" / "cuda" / "mps"
                 num_of_concurrent_executions: int = 2,
                 # The number of simultaneous executions for sentence generation tasks in the pre-trained language model
                 max_queue_size: int = 5,
                 # The maximum queue size for sentence generation tasks in the pre-trained language model
                 too_many_request_as_http_error=False,
                 # True: When a 'Too many requests' situation occurs, it returns the status as 429
                 use_mock_response=False,
                 # True: Returns fixed phrases for testing. As it doesn't need to load the model, it starts up immediately
                 mock_type="round",  # "round" / "long" - The type of phrases to return when use_mock_response=True
                 chat_prompt_clazz=None,
                 # Specifies the class that manages the prompts sent to the language model. Inherit from AbstractChatPrompt and implement a class that generates chat prompts according to the etiquette of each model
                 max_new_tokens=256,  # The maximum size of the newly generated tokens
                 context_len=1024,  # The size of the context (in terms of the number of tokens)
                 temperature=1.0,  # The temperature value for randomness in prediction
                 top_k=50,  # Value of top K for sampling
                 top_p=1.0,  # Value of top P for sampling
                 repetition_penalty=None,  # Penalty for repetition
                 repetition_penalty_method="multiplicative",  # Calculation method for repetition penalty
                 # Token related processing
                 add_special_tokens=None,  # Options for the tokenizer
                 request_handler=SimpleSessionRequestHandler(),
                 # Request handler. By default, a handler that simply keeps the session is default
                 logger=None,  # logging object
                 ):

        if logger is None:
            logger = logging.getLogger('chatstream')
            logger.setLevel(logging.NOTSET)
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s [%(name)s][%(levelname)s] #%(funcName)s  %(message)s'))

            logger.addHandler(handler)

        self.logger = logger

        self.request_handler = request_handler
        self.request_handler.logger = logger

        chat_params = {
            "temperature": temperature,  # 0.7,  # Temperatureの値
            "max_new_tokens": max_new_tokens,  # 新たに生成する最大トークンサイズ（何トークン分か。)
            "context_len": context_len,  ## コンテクストのサイズ（何トークン分か。)
            "use_top_k_sampling": top_k is not None,  # True: top K サンプリングを有効にする
            "top_k_value": top_k,  # top K サンプリングの値。
            "use_top_p_sampling": top_p is not None,  # True: top P サンプリングを有効にする
            "top_p_value": top_p,  # top P サンプリングの値
            "use_repetition_penalty": repetition_penalty is not None,  # True:繰り返し同じトークンを生成したときのペナルティを有効する
            "repetition_penalty": repetition_penalty is not None,  # ペナルティの値
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
        # サイズを +1 している理由は 次処理キューは　現在処理中（言語モデルにより文章生成中）のものと、次に処理にまわされるものの双方格納できるスペースのため
        self.run_on_next_queue = asyncio.Queue(maxsize=(num_of_concurrent_executions + 1))

        # 現在処理中(文章生成中)の リクエストタスク　が配置されている「処理中キュー」
        self.processing_queue = asyncio.Queue(maxsize=num_of_concurrent_executions)

        # コンソールチャット使用時のシングルユーザー用の ChatPrompt
        self.chat_prompt_for_single_user_on_console = None

        if use_mock_response:
            self.chat_generator = ChatGeneratorMock(model=None, tokenizer=None, device=None,
                                                    params={"mock_type": mock_type})
        else:
            self.chat_generator = ChatGenerator(model, tokenizer, device, chat_params)

        # request_handler にパラメータをセット
        request_handler.chat_generator = self.chat_generator
        request_handler.chat_prompt_clazz = self.chat_prompt_clazz

    async def handle_starlette_request(self, request: Request):
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

        set_req_id(request)  # ログ内で request の一意性を確認するために簡易idを振る

        # この request の処理待ち用カウントセマフォをつくる
        this_request_semaphore = asyncio.Semaphore(0)

        # 非同期操作の結果を保持するための Future オブジェクトをつくる
        future_result = asyncio.Future()

        try:
            # リクエストキュー（処理待ち行列）にリクエストタスク(request, this_request_semaphore, future_result)を追加する
            self.request_queue.put_nowait(
                (request, this_request_semaphore, future_result))  # put_nowait=>キューが一杯でない場合にのみ要求を追加
            self.logger.debug(f"{req_id(request)} このリクエストを'リクエストキュー'に追加")

        except asyncio.QueueFull:

            # リクエストキュー（処理ち行列）を超えるリクエストがあった場合はエラーを返す
            # クライアント側ではこのエラーを受け取ったたら、エラーの旨と、再送のボタンなどを表示する

            self.logger.debug(f"{req_id(request)} このリクエストを'リクエストキュー'に追加失敗。リクエストキューがいっぱい")
            if self.too_many_request_as_http_error:
                return JSONResponse(content={"error": "too_many_requests"}, status_code=429,
                                    media_type="application/json")
            else:
                return JSONResponse(content={"error": "too_many_requests"}, media_type="application/json")
        except Exception as e:
            # リクエスト処理中に想定していないエラーが発生した場合
            self.logger.warning(f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}")

            return JSONResponse(
                content={"error": "internal_server_error", "detail": "queueing request"}, status_code=500,
                media_type="application/json")

        # この request がリクエスト処理キューで処理されるのをまつ
        await this_request_semaphore.acquire()  # 処理待ち用カウントセマフォが releaseされるのを待つ / Wait for the waiting count semaphore to be released

        self.logger.debug(f"{req_id(request)} このリクエスト用セマフォは解放された")
        return await future_result

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

    async def queue_worker(self):
        """
        A worker for concurrently processing requests from clients. It manages the receipt, processing, and completion of requests.
        """
        self.logger.debug(f"キューワーカー開始")

        try:
            while True:
                # request_queue.get()　でクライアントからのリクエストが発生するのを待つ
                # クライアントからのリクエストが発生したとき
                # 即座にそのリクエストタスク（request, this_request_semaphore, future_resultのタプル）はリクエストキュー(request_queue)から取りだされ
                # 次実行キュー(run_on_next_queue) に詰められる
                request, this_request_semaphore, future_result = await self.request_queue.get()

                self.logger.debug(f"{req_id(request)} 'リクエストキュー'からリクエストタスク取り出し")

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
                self.run_on_next_queue.put_nowait((request, this_request_semaphore, future_result))

                self.logger.debug(f"{req_id(request)} リクエストタスクを'次処理キュー'に追加")

                # 同時処理カウントセマフォ(concurrent_processing_semaphore)を１つ取得
                await self.concurrent_processing_semaphore.acquire()

                request_task = await self.run_on_next_queue.get()  # 次実行キューを dequeue
                self.processing_queue.put_nowait(request_task)  # 処理中キューに enqueue

                self.logger.debug(f"{req_id(request)} リクエストタスク処理中： 実行権を獲得")

                async def request_processing_finished_callback(request, message):

                    """
                    文章生成ストリームの終了時に呼び出されるコールバック関数
                    ストリーム終了原因
                    ・message=="success" ストリームがクライアントに向け正常に送出された
                    ・message=="client_disconnected_1" ストリーム送出中にクライアントから切断された
                    ・message=="client_disconnected_2" ストリーム送出前にクライアントから切断されていた
                    ・message=="unknown_error_occurred" ストリーム送出中に予期せぬエラーが発生した
                    :param message:
                    :return:
                    """

                    # message は現在のところ、これより先には通知しない
                    # この結果を TODO 上位に伝えられるようにする
                    self.concurrent_processing_semaphore.release()  # 同時処理管理セマフォをリリースする Release the concurrent processing semaphore
                    await self.processing_queue.get()  # 現在の request を、リクエスト処理中キューから取り出す Get the current request from the request processing queue
                    self.logger.debug(f"{req_id(request)} リクエストタスク処理中： 文章生成終了　終了メッセージ:'{message}'")

                    # 上の2つ（セマフォと、キュー）を解放したので、次に処理されるべきリクエストタスクが処理(モデルによる文章生成)できるようになる。

                # concurrent_processing_semaphore を取得した request のみ、ここに入れる
                final_response = None
                try:
                    # request を処理する。responseは逐次出力を担当する StreamResponse になっているため、
                    # response を得たあともストリーミングが続いていることを忘れてはいけない

                    self.logger.debug(f"{req_id(request)} リクエストタスク処理中： リクエストハンドラにより処理開始")
                    final_response = await self.request_handler.process_request(request,
                                                                                streaming_finished_callback=request_processing_finished_callback)

                except ClientDisconnect as e:
                    # ストリーム送出開始時にクライアントから切断されていたとき

                    await request_processing_finished_callback(request, "client_disconnected_2")
                except Exception as e:
                    #  ストリーム送出開始時に想定していないエラーが発生したとき

                    self.logger.warning(f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}")

                    final_response = JSONResponse(
                        content={"error": "internal_server_error", "detail": "generating response"}, status_code=500,
                        media_type="application/json")

                    await request_processing_finished_callback(request, "unknown_error_occurred,while process_request")

                finally:
                    # response を 非同期用 result に詰めるが、
                    # response を return してもリクエスト処理がおわるわけではなく、クライアントへのストリーミングが継続することに
                    # 留意する必要がある。
                    future_result.set_result(final_response)

                    # リクエストの受付処理が終わったという意味で、セマフォを解放して URLエンドポイント側の処理に返す
                    # 上述のとおり、このタイミングではまだクライアントへストリーミングが継続しているため
                    # ストリーミング終了は
                    this_request_semaphore.release()

        except asyncio.CancelledError:
            print("Queue worker stopped.")
        except KeyboardInterrupt:
            print("Interrupted by user, shutting down.")
        except Exception as e:
            # リクエスト処理中に想定していないエラーが発生した場合
            print(f"予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}")

    def get_stats(self):
        """
        Return information about the current processing state (waiting state)
        """
        return {
            "processing": self.processing_queue.qsize(),
            "waiting": self.run_on_next_queue.qsize() + self.request_queue.qsize(),
            "_num_of_next_queue": self.run_on_next_queue.qsize(),
            "_num_of_request_queue": self.request_queue.qsize()
        }

    async def start_queue_worker(self):
        """
        Starts the queue worker and registers the force termination and shutdown handlers.
        """

        self.queue_worker_task = asyncio.create_task(self.queue_worker())  # キューワーカーを開始

        # 強制終了のシャットダウンハンドラを登録
        signal.signal(signal.SIGINT, lambda s, f: os._exit(0))
