from starlette.requests import Request

from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE


class ClientRoleWrapper:
    """
    ChatStream のコンストラクタに指定された user_role をラッピングして、各種操作を行う
    ・定義済「クライアントロール」リストが妥当が否か判定
    ・昇格コマンドがあるかどうかあらかじめ判定
    """

    def __init__(self, logger, eloc, client_roles=None):
        self.logger = logger
        self.eloc = eloc
        self.client_roles = client_roles

        self.browser_default_client_role = None
        self.agent_default_client_role = None

    def is_use_client_role_based_access_control(self):
        """
        ロールベースのアクセスコントロールを使用するか否か
        :return:
        """
        return self.client_roles is not None

    def is_browser_client_access(self, request: Request):
        """
        ブラウザクライアントからのアクセスか否か
        :param request:
        :return:
        """
        session_mgr = getattr(request.state, "session", None)
        return session_mgr is not None

    def get_browser_session(self, request: Request):
        """
        ブラウザクライアントからのアクセスのとき、そこに付与されたセッションを取得する
        :param request:
        :return:
        """
        session_mgr = getattr(request.state, "session", None)

        if session_mgr is None:
            self.logger.debug("session_mgr not exists")
            return None

        # セッションオブジェクト（辞書オブジェクト）を取得する
        session = session_mgr.get_session()
        return session

    def is_agent_client_access(self, request: Request):
        """
        エージェントクライアントからのアクセスか否か
        :param request:
        :return:
        """
        return not self.is_browser_client_access(request)

    def get_agent_current_client_role(self, request: Request):
        """
        エージェントクライアント の現在のロールを取得する
        ()
        :param request:
        :return:
        """
        if not hasattr(request.state, "__chatstream__"):
            request.state.__chatstream__ = {}

        client_role = request.state.__chatstream__.get(CHAT_STREAM_CLIENT_ROLE,None)

        return client_role

    def set_request_state(self,request,key,value):
        """
        ChatStream 用の request.state にキー、値を書き込む
        :param request:
        :param key:
        :param value:
        :return:
        """
        if not hasattr(request.state, "__chatstream__"):
            request.state.__chatstream__ = {}

        request.state.__chatstream__[key]=value

    def verify(self):
        """
        定義済「クライアントロール」リストが妥当か否かを確認する。
        ・ブラウザ用デフォルトロールが存在しない場合はエラー
        ・サーバー用デフォルトロールが存在しない場合はログのみ表示
        ・TODO フォーマットエラーの検出
        :return:
        """
        for role in self.client_roles.items():
            role_name = role[0]
            role_contents = role[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session")
            enable_dev_tool = apis.get("enable_dev_tool")

            if auth_method == "nothing" and use_session:  # デフォルトロール("nothing") かつ セッションあり(=ブラウザ用)
                # デフォルトロールがみつかったので、例外を投げずに戻る
                return True

        raise Exception(f"browser based default client role not found.Please specify default client role for browser.")

    def get_browser_default_client_role(self):
        """
        ブラウザからのアクセスクライアント用のデフォルトロールを、定義済クライアントロールリストの中から取得する
        :return:
        """

        if self.browser_default_client_role:
            # すでに、デフォルトロールがキャッシュされている場合はキャッシュをかえす
            return self.browser_default_client_role

        out = {}
        for role in self.client_roles.items():
            role_name = role[0]
            role_contents = role[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session", False)
            enable_dev_tool = apis.get("enable_dev_tool", False)

            if auth_method == "nothing" and use_session:  # デフォルトロール("nothing") かつ セッションあり(=ブラウザ用)
                out["enabled"] = True
                out["client_role_name"] = role_name
                out["allowed_apis"] = allow  # TODO "all"ならすべてのapiを入れる
                out["enable_dev_tool"] = enable_dev_tool

                self.logger.debug(self.eloc.to_str({
                    "en": f"Default role for browser definition found. role_name:{role_name}  allowed_apis:{allow}",
                    "ja": f"ブラウザ用デフォルトロールの定義を取得しました。 role_name:{role_name}  allowed_apis:{allow}"}))

                self.browser_default_client_role = out
                return out

        # ここを実行するということは、デフォルトロールがみつからなかった場合で、すでに verify メソッドで 例外が投げられている状態
        self.logger.debug(self.eloc.to_str({
            "en": f"Rolesare defined, but it appears that no default roles for browser are defined. In this case, unauthorized users will not be able to access ChatStream's API, effectively disabling ChatStream.",
            "ja": f"ロールの定義はありますが、ブラウザ用デフォルトロールが定義されていないようです。この場合、未認証ユーザーは ChatStream の API にアクセスできなくなるため、実質的に ChatStream が無効となります。"}))

        out["enabled"] = False
        self.browser_default_client_role = out
        return out

    def get_agent_default_client_role(self):
        """
        Agent からのアクセス(Agent = ブラウザではなくプログラムベースのクライアントという意味）
        クライアント用のデフォルトロールを、定義済クライアントロールリストの中から取得する
        :return:
        """

        if self.agent_default_client_role:
            # すでに、デフォルトロールがキャッシュされている場合はキャッシュをかえす
            return self.agent_default_client_role

        out = {}
        for role in self.client_roles.items():
            role_name = role[0]
            role_contents = role[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session", False)
            enable_dev_tool = apis.get("enable_dev_tool", False)

            if auth_method == "nothing" and not use_session:  # デフォルトロール("nothing") かつ セッションなし(=プログラムからのアクセス用)
                out["enabled"] = True
                out["client_role_name"] = role_name
                out["allowed_apis"] = allow  # TODO "all"ならすべてのapiを入れる
                out["enable_dev_tool"] = enable_dev_tool

                self.logger.debug(self.eloc.to_str({
                    "en": f"Default role for agent definition found. role_name:{role_name}  allowed_apis:{allow}",
                    "ja": f"エージェント用デフォルトロールの定義を発見しました。 role_name:{role_name}  allowed_apis:{allow}"}))

                self.agent_default_client_role = out
                return out

        # ここを実行するということは、デフォルトロールがみつからなかった場合で、すでに verify メソッドで 例外が投げられている状態
        self.logger.debug(self.eloc.to_str({
            "en": f"Roles are defined, but it appears that no default roles for agent are defined. In this case, unauthorized users will not be able to access ChatStream's API, effectively disabling ChatStream.",
            "ja": f"ロールの定義はありますが、エージェント用デフォルトロールが定義されていないようです。この場合、未認証ユーザーは ChatStream の API にアクセスできなくなるため、実質的に ChatStream が無効となります。"}))
        out["enabled"] = False
        self.agent_default_client_role = out

        return out
