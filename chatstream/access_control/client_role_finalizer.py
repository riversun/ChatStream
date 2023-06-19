from starlette.requests import Request

from chatstream.access_control.client_role_authorizer_for_agent import ClientRoleAuthorizerForAgent
from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE


class ClientRoleFinalizer:
    """
    現在アクセスされているリクエストに最終的なロールを付与する

    ・ブラウザからのアクセスの場合
        STEP 0.（default_client_role_grant_middleware.pyによりブラウザ用初期ロールが セッション にセットされる）
        STEP 1. (request_handlerにより、 user_input をハンドリングし必要に応じて昇格）
        STEP 2.（本クラスの役割）セッションに一時的に保持している現在のロールを request.state にセットしてロールの最終化を行う

    ・エージェントからのアクセスの場合
        STEP 0.（default_client_role_grant_middleware.pyによりエージェント用初期ロールが request.state にセットされる）
        STEP 1.（本クラスの役割）リクエストヘッダを確認し、別ロールに変更（昇格）できるか判定
        STEP 2.（本クラスの役割）昇格できた場合新たなロールを request.state にセットしロールの最終化を行う
    """

    def __init__(self, logger, eloc, client_role_wrapper=None):
        self.logger = logger
        self.eloc = eloc
        self.client_role_wrapper = client_role_wrapper
        self.agent_client_role_authorizer = ClientRoleAuthorizerForAgent(logger, eloc, client_role_wrapper=client_role_wrapper)  # リクエストヘッダーを分析し、昇格できるロールを返す

    def set_final_role(self, request: Request):
        """
        ロールを確定させる

        ・ブラウザクライアントの場合は、セッションに保存されている最新（最終）のクライアントロールを request.state 以下に保存する
        ・エージェントクライアントの場合は、昇格判定を行い、最終的なクライアントロールを request.state 以下に保存する
        :param request:
        :return:
        """
        is_browser_client_access = self.client_role_wrapper.is_browser_client_access(request)
        is_agent_client_access = self.client_role_wrapper.is_agent_client_access(request)
        if is_browser_client_access:
            self.handle_browser_client_access(request)
            pass
        elif is_agent_client_access:
            self.handle_agent_client_access(request)
            pass

        pass

    def handle_browser_client_access(self, request: Request):
        """
        ブラウザクライアントからのアクセスを処理する

        セッションに一時的に保持している現在のロールを request.state にセットしてロールの最終化を行う
        :param request:
        :return:
        """
        wrapper = self.client_role_wrapper
        # セッション（辞書オブジェクト）を取得する
        session = wrapper.get_browser_session(request)

        # セッションにある現在のロールを取得する
        crr_role = session.get(CHAT_STREAM_CLIENT_ROLE)
        #  crr_role={"client_role_name": "example_role", "allowed_apis": ["example1", "example2"]}

        # 最終的に request.state に保存する
        wrapper.set_request_state(request, CHAT_STREAM_CLIENT_ROLE, crr_role)

    def handle_agent_client_access(self, request: Request):
        """
        エージェントクライアントからのアクセスを処理する
        :param request:
        :return:
        """

        # エージェントクライアントの昇格を行う
        self.promote_agent_client_if_needed(request)

    def promote_agent_client_if_needed(self, request: Request):
        """
        エージェントクライアントの昇格を行う
        :param request:
        :return:
        """
        wrapper = self.client_role_wrapper
        promoted_role = self.agent_client_role_authorizer.get_promoted_role(request)
        if promoted_role:
            # ヘッダを解析した結果、新しいロールが存在したとき
            # 新しいロール(promoted_role) をセットする
            wrapper.set_request_state(request, CHAT_STREAM_CLIENT_ROLE, promoted_role)
