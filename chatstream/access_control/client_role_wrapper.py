from starlette.requests import Request

from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE
from chatstream.access_control.role_def_to_client_role import role_def_to_client_role
from chatstream.default_api_names import DefaultApiNames


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

        self.browser_default_client_role = None  # ブラウザ向けのデフォルトロールをキャッシュしておく
        self.agent_default_client_role = None  # エージェント向けのデフォルトロールをキャッシュしておく

        self.browser_client_roles_without_default = None
        self.agent_client_role_defs_without_default = None  # エージェント向けロール(デフォルトロール以外)をキャッシュしておく

        if self.client_roles is not None:
            self.verify()

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

        client_role = request.state.__chatstream__.get(CHAT_STREAM_CLIENT_ROLE, None)

        return client_role

    def set_request_state(self, request, key, value):
        """
        ChatStream 用の request.state にキー、値を書き込む
        :param request:
        :param key:
        :param value:
        :return:
        """
        if not hasattr(request.state, "__chatstream__"):
            request.state.__chatstream__ = {}

        request.state.__chatstream__[key] = value

    def get_request_state(self, request, key, default_value):
        """
        ChatStream 用の request.state から値を取り出す
        :param request:
        :param key:
        :param value:
        :return:
        """
        if not hasattr(request.state, "__chatstream__"):
            request.state.__chatstream__ = {}

        return request.state.__chatstream__.get(key,default_value)


    def verify(self):
        """
        定義済「クライアントロール」リストが妥当か否かを確認する。
        ・ブラウザ用デフォルトロールが存在しない場合はエラー
        ・サーバー用デフォルトロールが存在しない場合はログのみ表示
        ・TODO フォーマットエラーの検出
        :return:
        """

        is_browser_default_role_found = False
        is_agent_default_role_found = False
        for role_def in self.client_roles.items():
            role_name = role_def[0]
            role_contents = role_def[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session")
            enable_dev_tool = apis.get("enable_dev_tool")

            if allow is None:
                raise Exception("'allow' property should be set.")

            if allow != "all":
                if isinstance(allow, list):
                    for val in allow:
                        if val not in DefaultApiNames.API_NAMES:
                            raise ValueError(f"Invalid API name '{val}' in allow list. Allowed values are 'all' or any of {DefaultApiNames.API_NAMES}")
                else:
                    raise TypeError("Invalid type for allow. Expected 'all' or list of API names.")

            if auth_method == "nothing" and use_session:  # デフォルトロール("nothing") かつ セッションあり(=ブラウザ用)
                # デフォルトロールがみつかったので、例外を投げずに戻る
                if is_browser_default_role_found:
                    # 既にデフォルトロールが定義されているのに、2つ目が発見された
                    self.logger.debug(self.eloc.to_str({
                        "en": f"Several default roles are defined for the lauter. Only one default role can be defined",
                        "ja": f"ブラウザー用のデフォルトロールが複数定義されています。デフォルトロールは１つのみ定義可能です"}))
                    raise Exception(f"Several default roles are defined for the lauter. Only one default role can be defined.")

                is_browser_default_role_found = True

            if auth_method == "nothing" and not use_session:  # デフォルトロール("nothing") かつ セッションあり(=ブラウザ用)
                # デフォルトロールがみつかったので、例外を投げずに戻る

                is_agent_default_role_found = True

        if not is_browser_default_role_found:
            # ブラウザ用のデフォルトロールが定義されていないとき

            self.logger.debug(self.eloc.to_str({
                "en": f"Default role for browser not defined.",
                "ja": f"ブラウザー用のデフォルトロールが定義されていません。"}))
            raise Exception(f"browser based default client role not found.Please specify default client role for browser.")

        if not is_agent_default_role_found:
            # サーバー用のデフォルトロールが定義されていないとき
            # 必須ではないのでログのみ

            self.logger.debug(self.eloc.to_str({
                "en": f"Default role for the agent is not defined.",
                "ja": f"エージェント用のデフォルトロールは定義されていません。"}))

        return True

    def get_browser_default_client_role(self):
        """
        ブラウザからのアクセスクライアント用のデフォルトロールを、定義済クライアントロールリストの中から取得する
        :return:
        """

        if self.browser_default_client_role:
            # すでに、デフォルトロールがキャッシュされている場合はキャッシュをかえす
            return self.browser_default_client_role

        out = {}
        for role_def in self.client_roles.items():
            role_name = role_def[0]
            role_contents = role_def[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session", False)
            enable_dev_tool = apis.get("enable_dev_tool", False)

            if auth_method == "nothing" and use_session:  # デフォルトロール("nothing") かつ セッションあり(=ブラウザ用)
                out = role_def_to_client_role(role_def)
                out["enabled"] = True
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
        for role_def in self.client_roles.items():
            role_name = role_def[0]
            role_contents = role_def[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session", False)
            enable_dev_tool = apis.get("enable_dev_tool", False)

            if auth_method == "nothing" and not use_session:  # デフォルトロール("nothing") かつ セッションなし(=プログラムからのアクセス用)
                out = role_def_to_client_role(role_def)
                out["enabled"] = True

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

    def get_agent_special_role_defs(self):
        """
        エージェント用のロールを取得する
        ・セッション無効のもの
        ・デフォルトロールは含めない

        :return:
        """

        if self.agent_client_role_defs_without_default is None and self.client_roles is not None:
            # エージェントクライアント用のロール定義(デフォルトロール以外)のキャッシュがまだない場合
            role_defs = []
            for role_def in self.client_roles.items():
                role_name = role_def[0]
                role_contents = role_def[1]
                apis = role_contents.get("apis")
                allow = apis.get("allow")
                auth_method = apis.get("auth_method")
                use_session = apis.get("use_session", False)
                enable_dev_tool = apis.get("enable_dev_tool", False)

                if auth_method != "nothing" and not use_session:  # デフォルトロール("nothing") かつ セッションなし(=プログラムからのアクセス用)

                    role_defs.append(role_def)

            self.agent_client_role_defs_without_default = role_defs

        return self.agent_client_role_defs_without_default

    def get_browser_special_role_defs(self):
        """
        ブラウザクライアント用のロールを取得する
        ・セッション有効のもの
        ・デフォルトロールは含めない

        :return:
        """

        if self.browser_client_roles_without_default is None:
            role_defs = []
            for role_def in self.client_roles.items():
                role_name = role_def[0]
                role_contents = role_def[1]
                apis = role_contents.get("apis")
                allow = apis.get("allow")
                auth_method = apis.get("auth_method")
                use_session = apis.get("use_session", False)
                enable_dev_tool = apis.get("enable_dev_tool", False)

                if auth_method != "nothing" and use_session:  # デフォルトロール("nothing") かつ セッションなし(=プログラムからのアクセス用)

                    role_defs.append(role_def)

            self.browser_client_roles_without_default = role_defs

        return self.browser_client_roles_without_default
