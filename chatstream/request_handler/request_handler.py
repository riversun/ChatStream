import asyncio
from abc import ABC, abstractmethod

from fastapi import Request
import traceback


class AbstractRequestHandler(ABC):
    """
    リクエストハンドラの基底抽象クラス
    本クラスを継承した独自のリクエストハンドラを作成し、

    process_request　をオーバーライドすることで以下のような要件を実装できる
    
    - ログインしたユーザーの会話履歴の永続化
    - 未ログインでも一定期間、コンテクストを維持した会話の継続
    
    また、Pythonエコシステム外で認証やフロントエンド、フロントサーバーを作成する場合では、
    VPC等などバックエンド側に立てた chat_stream plugged な FastAPI サーバーに
    フロントサーバーのリクエストをリバースプロキシ的にバイパスする。
    その際、リクエストヘッダー等、バックエンド側に伝えられる手段で chat_prompt を一意に識別できるキーを付与し
    RequestHandler 側で chat_prompt の復元（MongoDB等サーバーから) をし、生成終了時に更新することで、
    無理に Pythonでフロントまでをカバーする必要はない。
    
    """

    def __init__(self):
        self.chat_generator = None
        self.chat_prompt_clazz = None
        self.logger = None

    async def generate(self, chat_prompt, chat_generation_finished_callback):
        f"""
        事前学習済言語モデルから逐次生成されたトークンを送出する非同期ジェネレーターを返す
        
        非同期ジェネレーターにより逐次トークンが生成され最終的に
        クライアントへのレスポンスストリームに送出されるが、
        その送出中にクライアント側からの切断が検出された場合、コールバック関数に "client_disconnected_1"
        をコールバックする
        
        :param chat_prompt: 
        :param chat_generation_finished_callback: 事前学習済言語モデルでの文章生成終了時に受け取るコールバック関数
        コールバック関数のパラメータは message
        文章生成状況に応じて、コールバックされるパラメータは以下の通りとなる
        
        "success" ... 文章生成が無事終了
        "client_disconnected_1" ... レスポンス送出中にクライアントからの切断またはネットワーク切断が発生した
        "unknown_error" ... 文章生成中に予期せぬエラーが発生した場合
        :return:                                 
        """

        # chat_generator.generate をラッピングすることで、 CancelledError をキャッチしてコールバックできるようにしている
        try:
            async for tok in self.chat_generator.generate(chat_prompt,
                                                          {"output_type": "response_text",
                                                           "post_process_callback": chat_generation_finished_callback
                                                           }):
                yield tok
        except asyncio.CancelledError:
            # レスポンス送出中にクライアントからの切断が発生した場合
            # request 処理が異常終了(送出中にクライアントからの切断、ネットワーク断)したことを指定されたコールバック関数に通知
            await chat_generation_finished_callback("client_disconnected_1")

        except Exception as e:
            #  ストリーム送出開始時に想定していないエラーが発生したとき
            print(f"予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}")
            await chat_generation_finished_callback("unknown_error_occurred,while chat_generator.generate")

    @abstractmethod
    async def process_request(self, request: Request, streaming_finished_callback):
        pass
