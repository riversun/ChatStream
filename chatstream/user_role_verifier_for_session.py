class UserRoleVerifierForSession:
    """
    アクセス中のユーザーのHTTPセッションに格納されたロール情報が
    あるリソース(Web API) へのアクセス権限(privileges) を持つか否かを判定する
    """

    def __init__(self, logger, eloc, api_access_role=None):
        self.logger = logger
        self.eloc = eloc
        self.api_access_role = api_access_role

    def verify_role_has_privilege(self, request, api_name):
        if self.api_access_role is None:
            return {"allowed": True, "detail": "api_access_role is None"}

        session_mgr = getattr(request.state, "session", None)

        if session_mgr:
            # セッションオブジェクト（辞書オブジェクト）を取得する
            session = session_mgr.get_session()
            role_name = session.get("user_role_name")  # 現在アクセスしているユーザーが持つロール名
            allowed_apis = session.get("allowed_apis")  # 現在アクセスユーザーが保有するAPIアクセス権

            if allowed_apis is None:
                return {"allowed": False, "detail": "allowed_apis not defined."}

            if isinstance(allowed_apis, str):
                # allowed_apisが文字列型の場合、allowed_apisとapi_nameが一致するか否かを確認
                if allowed_apis == api_name or api_name == "all":
                    return {"allowed": True, "detail": f"api_name:{api_name} is matched with allowed_apis(str)"}
                else:
                    return {"allowed": False, "detail": f"api_name:{api_name} is NOT matched with allowed_apis(str)"}
            elif isinstance(allowed_apis, list):
                # allowed_apisがリスト型の場合、そのリストの中にapi_nameが含まれているか否かを判定
                if api_name in allowed_apis:
                    return {"allowed": True, "detail": f"api_name:{api_name} is in allowed_apis(list)."}
                else:
                    return {"allowed": False, "detail": f"api_name:'{api_name}' is NOT in allowed_apis(list)."}
            else:
                raise Exception(f"allowed_apis should be either string or list.")

        else:
            # セッションが無効な場合
            raise Exception(f"Session is not available.")
