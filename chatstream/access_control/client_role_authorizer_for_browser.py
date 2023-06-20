import hashlib

from starlette.requests import Request

from chatstream.access_control.role_def_to_client_role import role_def_to_client_role


class ClientRoleAuthorizerForBrowser:
    """
    ブラウザクライアントのロールの認証処理を行う

    request または　user_input を解析して、ロール定義(client_roles)で定義されているロールに該当する
    クレデンシャルが含まれいるか判定をし、含まれていれば照合処理を行い、成功すれば、
    そのクレデンシャルに該当する新規ロールを返す

    クレデンシャルの認証方法は以下が存在する
    "ui_pass_phrase" ... user_input に入力されたテキストがあらかじめ指定したものであった場合
    "ui_pass_phrase_sha256" ... user_input に入力されたテキストの SHA256 があらかじめ指定したものであった場合

    同一の認証方法で複数定義することも可能。

    """

    def __init__(self, logger, eloc, client_role_wrapper=None):
        self.logger = logger
        self.eloc = eloc
        self.client_role_wrapper = client_role_wrapper
        self.browser_client_roles = client_role_wrapper.get_browser_special_role_defs()

    def get_promoted_role(self, request: Request, user_input):

        for role_def in self.browser_client_roles:
            role_name = role_def[0]
            role_contents = role_def[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session", False)
            enable_dev_tool = apis.get("enable_dev_tool", False)

            if auth_method == "ui_pass_phrase":

                if user_input is None or user_input == "":
                    return None

                phrase = apis.get("ui_pass_phrase")
                if user_input == phrase:  # 認可処理
                    self.logger.debug(f"auth_method:{auth_method} authorized.")
                    client_role = role_def_to_client_role(role_def)
                    return client_role  # 認可されたロールを返す

            elif auth_method == "ui_pass_phrase_sha256":

                phrase_sha256 = apis.get("ui_pass_phrase_sha256")
                user_input_encoded = hashlib.sha256(user_input.encode()).hexdigest()

                if phrase_sha256 == user_input_encoded:  # 認可処理
                    self.logger.debug(f"auth_method:{auth_method} authorized")
                    client_role = role_def_to_client_role(role_def)
                    return client_role  # 認可されたロールを返す

            else:
                raise Exception(f"Unknown browser auth method: '{auth_method}'")

        return None
