import asyncio
from abc import ABC, abstractmethod

from fastapi import Request
import traceback

from chatstream.access_control.client_role_authorizer_for_browser import ClientRoleAuthorizerForBrowser
from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE
from chatstream.default_finish_token import DEFAULT_FINISH_TOKEN
from chatstream.util_create_streaming_response import create_streaming_response
from chatstream.util_request_id import req_id


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
        self.eloc = None
        self.client_role_wrapper = None

    async def generate(self, chat_prompt, chat_generation_finished_callback, request, custom_generation_params, message_id=None):
        f"""
        事前学習済言語モデルから逐次生成されたトークンを送出する非同期ジェネレーターを返す
        
        非同期ジェネレーターにより逐次トークンが生成され最終的に
        クライアントへのレスポンスストリームに送出されるが、
        その送出中にクライアント側からの切断が検出された場合、コールバック関数に "client_disconnected_while_streaming"
        をコールバックする
        
        :param chat_prompt: 
        :param chat_generation_finished_callback: 事前学習済言語モデルでの文章生成終了時に受け取るコールバック関数
        コールバック関数のパラメータは message
        文章生成状況に応じて、コールバックされるパラメータは以下の通りとなる
        
        "success" ... 文章生成が無事終了
        "client_disconnected_while_streaming" ... レスポンス送出中にクライアントからの切断またはネットワーク切断が発生した
        "unknown_error" ... 文章生成中に予期せぬエラーが発生した場合
        :return:                                 
        """

        # chat_generator.generate をラッピングすることで、 CancelledError をキャッチしてコールバックできるようにしている
        try:
            async for tok in self.chat_generator.generate(chat_prompt,
                                                          {"output_type": "response_text",
                                                           "post_process_callback": chat_generation_finished_callback,
                                                           # 個々に設定できる生成パラメータ
                                                           "generation_params": custom_generation_params,
                                                           "message_id": message_id
                                                           }):
                yield tok
        except asyncio.CancelledError:
            # レスポンス送出中にクライアントからの切断が発生した場合
            # request 処理が異常終了(送出中にクライアントからの切断、ネットワーク断)したことを指定されたコールバック関数に通知
            await chat_generation_finished_callback("client_disconnected_while_streaming")

        except Exception as e:
            #  ストリーム送出開始時に想定していないエラーが発生したとき

            self.logger.warning(f"{req_id(request)} 予期せぬエラーが発生しました: {e}\n{traceback.format_exc()}")

            # エラーのコールバックを返す
            await chat_generation_finished_callback("unknown_error_occurred,while chat_generator.generate")

            # エラーを上位に投げる
            # (このエラーは、generator が yield しはじめた場合、上位にあがらない)
            raise e

    def detect_special_command_for_role_promotion(self, request, user_input, streaming_finished_callback):
        """
        ロール昇格のための特殊コマンドが入力されているかどうか確認し、入力されていれば、
        昇格したロールをセッションに保存し、レスポンスを返す

        ロールの昇格がなければ None をかえす
        :param request:
        :param user_input:
        :param streaming_finished_callback:
        :return:
        """
        new_role_result = self.verify_user_input_for_role_promotion(request, user_input)
        is_new_role_granted = new_role_result.get("is_new_role_granted")

        if is_new_role_granted is True:
            # 新しいロールが付与された場合
            new_role = new_role_result.get("new_role")
            client_role_name = new_role.get("client_role_name")
            allowed_apis = new_role.get("allowed_apis")
            enable_dev_tool = new_role.get("enable_dev_tool", False)

            headers = None

            if enable_dev_tool:
                headers = {"X-ChatStream-API-DevTool-Enabled": "enabled"}

            eos_token = DEFAULT_FINISH_TOKEN

            streaming_response = create_streaming_response(
                request,
                f"New role: '{client_role_name}' has been granted",
                streaming_finished_callback,
                headers=headers,
                eos_token=eos_token)

            return streaming_response

        return None

    def verify_user_input_for_role_promotion(self, request, user_input):
        """
        user_inputや、request をみて、新ロールを付与する
        """

        self.logger.debug(f"#handle_access_role xxxx ロール判定 user_input:{user_input}")

        client_role_auth_for_browser = ClientRoleAuthorizerForBrowser(
            logger=self.logger,
            eloc=self.eloc,
            client_role_wrapper=self.client_role_wrapper)

        # request,user_input が特定のキーワードの場合、新ロール（＝おおくのばあい昇格ロールであるべき）を取得する
        new_role = client_role_auth_for_browser.get_promoted_role(request, user_input)

        if new_role is not None:
            # 昇格ロールが存在するとき
            session = self.client_role_wrapper.get_browser_session(request)
            session[CHAT_STREAM_CLIENT_ROLE] = new_role  # 新たなロールをセットする
            return {"is_new_role_granted": True, "new_role": new_role}

        return {"is_new_role_granted": False, "new_role": None}

    @abstractmethod
    async def process_request(self, request: Request, streaming_finished_callback):
        pass

    @abstractmethod
    def get_request_handler_type(self):
        pass
