from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from chatstream.util_request_id import req_id

CHAT_STREAM_CLIENT_ROLE = "chat_stream_client_role"


class DefaultClientRoleGrantMiddleware(BaseHTTPMiddleware):
    """
    まだ、現在アクセスしているクライアントのロールがまだ設定されていないとき、
    このクライアントにデフォルトのロールの割り当てるミドルウェア
    """

    def __init__(self, app, chat_stream):
        super().__init__(app)
        # self.client_roles = chat_stream.client_roles
        self.client_role_wrapper = chat_stream.client_role_wrapper
        self.eloc = chat_stream.eloc
        self.logger = chat_stream.logger
        self.logger.debug(
            self.eloc.to_str(
                {
                    "en": f"DefaultClientRoleGrantMiddleware initialized ",
                    "ja": f"DefaultClientRoleGrantMiddleware を初期化しました"}))

    async def dispatch(self, request: Request, call_next):
        self.logger.debug(
            self.eloc.to_str(
                {
                    "en": f"{req_id(request)} Default client role grant started",
                    "ja": f"{req_id(request)} デフォルトのクライアントロール付与を開始します"}))
        # 認証パターン３つ
        # (1) ロールが未定義
        # (2) ロール定義済で HTTPセッションが有効（ブラウザからのアクセスとみなす)
        # (3) ロール定義済で HTTPセッションが無効（サーバーからのアクセスとみなす)

        if not self.client_role_wrapper.is_use_client_role_based_access_control():
            # - (1) ロールが未定義 => ChatStreamコンストラクタでロール定義をしていないとき

            # ロールの概念は存在せず、現実的にどのAPIにもフルアクセスができる
            self.logger.debug(
                self.eloc.to_str(
                    {
                        "en": f"{req_id(request)} client_role definition is not found. Access control by role is disabled.",
                        "ja": f"{req_id(request)} ロール定義がありません。ロールによるアクセスコントロールは無効です"}))
            response = await call_next(request)
            return response

        elif self.client_role_wrapper.is_browser_client_access(request):
            # - (2) ロール定義済で HTTPセッションが有効（ブラウザからのアクセスとみなす)

            self.logger.debug(
                self.eloc.to_str(
                    {
                        "en": f"{req_id(request)} Requesting {request.url} browser client detected",
                        "ja": f"{req_id(request)} {request.url} へのリクエスト中 ブラウザクライアントからのアクセスと判定しました"}))
            # ブラウザからのユーザーアクセス用のデフォルトロールを付与する
            await self.grant_browser_default_role_if_needed(request)

        else:
            # - (3) ロール定義済で HTTPセッションが無効（サーバーからのアクセスとみなす)
            # （FastSession がリクエストに含まれる　特殊ヘッダー　により、明示的にスキップされた場合、セッション情報が request.state に付与されないため、HTTPセッションが存在しないと判定される）
            self.logger.debug(
                self.eloc.to_str(
                    {
                        "en": f"{req_id(request)} Requesting {request.url} agent client detected",
                        "ja": f"{req_id(request)} {request.url} へのリクエスト中 エージェントクライアントからのアクセスと判定しました"}))

            # エージェント(ブラウザ以外のプログラムコードなど）からのアクセス用のデフォルトロールを付与する
            await self.grant_agent_default_role(request)

        response = await call_next(request)

        return response

    async def grant_browser_default_role_if_needed(self, request):
        """
        ブラウザからのユーザーアクセス用のデフォルトロールを付与する
        :param request:
        :param session_mgr:
        :return:
        """

        # セッション（辞書オブジェクト）を取得する
        session = self.client_role_wrapper.get_browser_session(request)

        # セッションに現在のロール名があるかどうか確認
        crr_role = session.get(CHAT_STREAM_CLIENT_ROLE)

        self.logger.debug(
            self.eloc.to_str(
                {
                    "en": f"{req_id(request)} Browser client requesting {request.url} Get current role from session. session['{CHAT_STREAM_CLIENT_ROLE}'] => crr_role:{crr_role}",
                    "ja": f"{req_id(request)}  {request.url}へのリクエスト中 ブラウザクライアントの現在のセッションから現在のロールを取得します session['{CHAT_STREAM_CLIENT_ROLE}'] => crr_role:{crr_role}"}))

        if crr_role is None:
            # - 今アクセスしているブラウザクライアントに現在のロールがセットされていないとき
            browser_default_client_role = self.client_role_wrapper.get_browser_default_client_role()

            default_role_exists = browser_default_client_role.get("enabled", False)

            if default_role_exists:
                # - ブラウザクライアントのデフォルトロールが存在するとき

                # 現在アクセス中のブラウザクライアントのセッションに、ロール情報をセットする

                browser_default_role = browser_default_client_role.copy()
                browser_default_role.pop("enabled", None)  # 削除する
                session[CHAT_STREAM_CLIENT_ROLE] = browser_default_role

                role_name = browser_default_role.get("client_role_name")
                allowed_apis = browser_default_role.get("allowed_apis")
                enable_dev_tool = browser_default_role.get("enable_dev_tool")

                self.logger.debug(
                    self.eloc.to_str(
                        {
                            "en": f"{req_id(request)} Browser client requesting {request.url} Current role not set yet so default role '{role_name}' set. Allowed APIs will be '{allowed_apis}' enable_dev_tool:{enable_dev_tool}",
                            "ja": f"{req_id(request)} ブラウザクライアントは {request.url}へのリクエスト中 現在のロールはまだセットされていないので、デフォルトロール '{role_name}' をセットしました。許可された API は '{allowed_apis}' となります enable_dev_tool:{enable_dev_tool}"}))
            else:
                # - ブラウザクライアントのデフォルトロールが存在しないとき

                self.logger.debug(
                    self.eloc.to_str(
                        {
                            "en": f"{req_id(request)} Browser client requesting {request.url} Current role not set yet so attempt to set default role but default role doesn't exist.",
                            "ja": f"{req_id(request)} ブラウザクライアントは {request.url}へのリクエスト中 現在のロールはまだセットされていないため、デフォルトロールをセットしようとしましたが、デフォルトロールは定義されていませんでした。"}))
                # 別の場所でハンドリングされているのでここはスルーでoK
                pass

        else:
            # - 現在アクセスしているユーザーには既にロールが割り当てられているとき

            role_name = crr_role.get("client_role_name")
            allowed_apis = crr_role.get("allowed_apis")
            enable_dev_tool = crr_role.get("enable_dev_tool")
            self.logger.debug(
                self.eloc.to_str(
                    {
                        "en": f"{req_id(request)} Browser client requesting {request.url} User has privileges for role '{crr_role}'. Allowed APIs are '{allowed_apis}'.",
                        "ja": f"{req_id(request)} ブラウザクライアントは {request.url}へのリクエスト中 クライアントは既にロール '{crr_role}' の権限を保有しています。許可された API は '{allowed_apis}' となります"}))

    async def grant_agent_default_role(self, request):
        """
        エージェントからのアクセス用のデフォルトロールを付与する
        :param request:
        :return:
        """

        # エージェントのデフォルトロールを取得する
        agent_default_client_role = self.client_role_wrapper.get_agent_default_client_role()
        default_role_exists = agent_default_client_role.get("enabled", False)

        if default_role_exists:
            # - エージェントクライアントのデフォルトロールが存在するとき

            # 現在アクセス中のブラウザクライアントのセッションに、ロール情報をセットする

            # ChatStream 用の request.state にキー、値を書き込む
            client_role = agent_default_client_role.copy()
            client_role.pop("enabled", None)  # 削除する
            self.client_role_wrapper.set_request_state(request, CHAT_STREAM_CLIENT_ROLE, client_role)

            role_name = client_role.get("client_role_name")
            allowed_apis = client_role.get("allowed_apis")
            self.logger.debug(
                self.eloc.to_str(
                    {
                        "en": f"{req_id(request)} Agent client requesting {request.url} Default role for agent '{role_name}' set allowed_apis:{allowed_apis}",
                        "ja": f"{req_id(request)} {request.url}へのリクエスト中 エージェント用のデフォルトロール '{role_name}'をセットしました allowed_apis:{allowed_apis}"
                    }))


        else:
            # - エージェントのデフォルトロールが存在しないとき
            self.logger.debug(
                self.eloc.to_str(
                    {
                        "en": f"{req_id(request)} Agent client requesting {request.url} Agent default role doesn't exist.",
                        "ja": f"{req_id(request)} エージェントクライアントが {request.url} へのリクエスト中 エージェント用のデフォルトロールは定義されていません。"
                    }))
