import hashlib

from starlette.requests import Request

from chatstream.access_control.role_def_to_client_role import role_def_to_client_role


class ClientRoleAuthorizerForAgent:
    """
    エージェントクライアントのロールの認証処理を行う

    request を解析して、ロール定義(client_roles)で定義されているロールに該当する
    クレデンシャルが含まれいるか判定をし、含まれていれば照合処理を行い、成功すれば、
    そのクレデンシャルに該当する新規ロールを返す

    本クラスはエージェントクライアント用なので基本的に リクエストヘッダーの認証処理を行う

    エージェントクライアントは HTTP リクエストヘッダーに "X-ChatStream-Auth-Header" を付与し、そこにクレデンシャルを格納する

    クレデンシャルの認証方法は以下が存在する
    "header_phrase" ... 生テキストで認証
    "header_phrase_sha256" ... サーバー側にSHA256ハッシュを保存する

    同一の認証方法で複数定義することも可能。

    """

    def __init__(self, logger, eloc, client_role_wrapper=None):
        self.logger = logger
        self.eloc = eloc
        self.client_role_wrapper = client_role_wrapper
        self.agent_client_roles = client_role_wrapper.get_agent_special_role_defs()

    def get_promoted_role(self, request: Request):

        for role_def in self.agent_client_roles:
            role_name = role_def[0]
            role_contents = role_def[1]
            apis = role_contents.get("apis")
            allow = apis.get("allow")
            auth_method = apis.get("auth_method")
            use_session = apis.get("use_session", False)
            enable_dev_tool = apis.get("enable_dev_tool", False)

            if auth_method == "header_phrase":

                request_auth_header_text = request.headers.get("X-ChatStream-Auth-Header")
                if request_auth_header_text is None:
                    return None

                header_phrase = apis.get("header_phrase")
                if request_auth_header_text == header_phrase:  # 認可処理
                    self.logger.debug(f"auth_method:{auth_method} matched and role_name:'{role_name}' resolved")
                    client_role = role_def_to_client_role(role_def)
                    return client_role  # 認可されたロールを返す

            elif auth_method == "header_phrase_sha256":
                request_auth_header_text = request.headers.get("X-ChatStream-Auth-Header")

                if request_auth_header_text is None:
                    return None

                header_phrase_encoded = apis.get("header_phrase")
                request_auth_header_encoded = hashlib.sha256(request_auth_header_text.encode()).hexdigest()

                if request_auth_header_encoded == header_phrase_encoded:  # 認可処理
                    self.logger.debug(f"auth_method:{auth_method} matched and role_name:'{role_name}' resolved")
                    client_role = role_def_to_client_role(role_def)
                    return client_role  # 認可されたロールを返す

            else:
                raise Exception(f"Unknown agent auth method: '{auth_method}'")

        return None
