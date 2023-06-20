import uuid

from starlette.requests import Request


def req_id(request: Request):
    """
    開発時デバッグロギング用途で Request を識別する簡易ID を振る
    :param request:
    :return:
    """
    session_mgr = getattr(request.state, "session", None)

    if session_mgr is not None:
        req_id = session_mgr.get_session_id()[-4:]
        if not hasattr(request.state, "__chatstream__"):
            request.state.__chatstream__ = {}
        request.state.__chatstream__["req_id"] = req_id
        return f"req_id_{request.state.__chatstream__['req_id']}"
    else:
        # セッションが使えない場合
        if not hasattr(request.state, "__chatstream__"):
            request.state.__chatstream__ = {}
        request.state.__chatstream__["req_id"] = str(uuid.uuid4())[-4:]  # 下4桁
        return f"req_id_NOSESSION_{request.state.__chatstream__['req_id']}"


