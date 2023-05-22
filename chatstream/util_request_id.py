from starlette.requests import Request
import uuid


def set_req_id(request: Request):
    """
    開発時デバッグロギング用途で Request を識別する簡易ID を振る

    本番運用の場合は、OpenID や 自前生成の UUID など一意IDを別途セッションなどで格納しログ分析することを推奨する
    :param request:
    :return:
    """
    if not hasattr(request.state, "__chatstream__"):
        request.state.__chatstream__ = {}
    request.state.__chatstream__["req_id"] = str(uuid.uuid4())


def req_id(request: Request):
    """
    開発時デバッグロギング用途で Request を識別する簡易ID を振る
    :param request:
    :return:
    """
    return f"req_id_{request.state.__chatstream__.get('req_id', '0000')[-4:]}"  # 下4桁
