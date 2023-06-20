from starlette.requests import Request

from chatstream.access_control.client_role_finalizer import ClientRoleFinalizer
from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE
from chatstream.default_api_names import DefaultApiNames


class ClientRoleVerifier:
    """
    現在のリクエストにおいて、
    あるAPIにアクセス可能か否かを判定する
    """

    def __init__(self, chat_stream):
        self.logger = chat_stream.logger
        self.eloc = chat_stream.eloc
        self.client_role_wrapper = chat_stream.client_role_wrapper

        self.finalizer = ClientRoleFinalizer(logger=self.logger, eloc=self.eloc, client_role_wrapper=self.client_role_wrapper)

    def verify_client_role(self, request: Request, api_name):
        """
        指定した api_name が現在のロールでアクセス可能かどうか を検証する
        :param request:
        :param api_name:
        :return:
        """
        wrapper = self.client_role_wrapper
        self.finalizer.set_final_role(request)

        final_client_role = wrapper.get_request_state(request, CHAT_STREAM_CLIENT_ROLE, None)

        if api_name not in DefaultApiNames.API_NAMES:
            return {"success": False, "message": f"Invalid api_name:'{api_name}'. api_name should any of {DefaultApiNames.API_NAMES}"}

        allowed_apis = final_client_role.get("allowed_apis")
        client_role_name = final_client_role.get("client_role_name")

        if allowed_apis is None:
            return {"success": False, "message": f"'allow' property should be set."}

        is_verified = False

        if allowed_apis == "all":
            is_verified = True

        elif isinstance(allowed_apis, list):
            if api_name in allowed_apis:
                is_verified = True

        else:
            return {"success": False, "message": f"Invalid type for allowed_apis:{allowed_apis}. Expected 'all' or list of API names."}

        return {"success": is_verified, "message": ""}
