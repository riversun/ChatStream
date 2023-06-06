from starlette.requests import Request
import uuid


def set_req_id(request: Request):
    """
    開発時デバッグロギング用途で Request を識別する簡易ID を振る

    本番運用の場合は、OpenID や 自前生成の UUID など一意IDを別途セッションなどで格納しログ分析することを推奨する
    :param request:
    :return:
    """
    session_mgr = getattr(request.state, "session", None)
    if session_mgr is not None:
        req_id = session_mgr.get_session_id()[-4:]

        if not hasattr(request.state, "__chatstream__"):
            request.state.__chatstream__ = {}

        request.state.__chatstream__["req_id"] = req_id
    else:
        request.state.__chatstream__["req_id"] = str(uuid.uuid4())[-4:]  # 下4桁


def req_id(request: Request):
    """
    開発時デバッグロギング用途で Request を識別する簡易ID を振る
    :param request:
    :return:
    """
    return f"req_id_{request.state.__chatstream__['req_id']}"
