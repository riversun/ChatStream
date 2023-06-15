import pytest
from fastapi import FastAPI

from unittest.mock import Mock

from fastapi.routing import APIRoute

from chatstream import ChatStream
from chatstream.chat_stream_api_appender import append_apis
from chatstream.default_api_names import DefaultApiNames
from chatstream.default_api_names_to_path import to_web_api_path


# テスト対象のChatStreamをモック化
class MockChatStream:
    allow_get_prompt = True


def test_route_get_prompt_included():
    # モックのChatStreamとFastAPIアプリケーションインスタンスを作成
    chat_stream = ChatStream()
    app = FastAPI()

    # append_apisを呼び出し、"get_prompt"を含むAPIを追加
    append_apis(chat_stream, app, {"include": [DefaultApiNames.GET_PROMPT]}, Mock(), Mock())

    # ルートリストからAPIRouteインスタンスを取得
    routes = [route for route in app.routes if isinstance(route, APIRoute)]

    # get_promptのパスがルートに含まれていることを確認
    assert any(route.path == to_web_api_path(DefaultApiNames.GET_PROMPT) for route in routes), "APIパス 'get_prompt' が見つからない"

    # get_prompt以外のパスがルートに含まれていないことを確認
    other_api_names = [api_name for api_name in DefaultApiNames.API_NAMES if api_name != DefaultApiNames.GET_PROMPT]
    for api_name in other_api_names:
        assert not any(route.path == to_web_api_path(api_name) for route in routes), f"APIパス '{api_name}' が存在する"


def test_route_all_included_except_excluded():
    # モックのChatStreamとFastAPIアプリケーションインスタンスを作成
    chat_stream = ChatStream()
    app = FastAPI()

    # append_apisを呼び出し、"all"を含むAPIを追加し、指定したAPIを除外
    excluded_api_names = [DefaultApiNames.GET_PROMPT, DefaultApiNames.CLEAR_CONTEXT]
    append_apis(chat_stream, app, {"exclude": excluded_api_names}, Mock(), Mock())

    # ルートリストからAPIRouteインスタンスを取得
    routes = [route for route in app.routes if isinstance(route, APIRoute)]

    # 指定されたAPI以外の全てのAPIがルートに追加されていることを確認
    included_api_names = [api_name for api_name in DefaultApiNames.API_NAMES if api_name not in excluded_api_names]
    for api_name in included_api_names:
        assert any(route.path == to_web_api_path(api_name) for route in routes), f"APIパス '{api_name}' が見つからない"

    # 指定されたAPIがルートに含まれていないことを確認
    for api_name in excluded_api_names:
        assert not any(route.path == to_web_api_path(api_name) for route in routes), f"APIパス '{api_name}' が存在する"

def test_route_all_included_when_all_specified():
    # モックのChatStreamとFastAPIアプリケーションインスタンスを作成
    chat_stream = ChatStream()
    app = FastAPI()

    # append_apisを呼び出し、"all"を指定
    append_apis(chat_stream, app, {"all": True}, Mock(), Mock())

    # ルートリストからAPIRouteインスタンスを取得
    routes = [route for route in app.routes if isinstance(route, APIRoute)]

    # 全てのAPIがルートに追加されていることを確認
    for api_name in DefaultApiNames.API_NAMES:
        assert any(route.path == to_web_api_path(api_name) for route in routes), f"APIパス '{api_name}' が見つからない"

def test_error_when_all_and_include_specified():
    # モックのChatStreamとFastAPIアプリケーションインスタンスを作成
    chat_stream = ChatStream()
    app = FastAPI()

    # "all"と"include"を同時に指定してappend_apisを呼び出し、エラーが発生することを確認
    with pytest.raises(ValueError):
        append_apis(chat_stream, app, {"all": True, "include": [DefaultApiNames.GET_PROMPT]}, Mock(), Mock())
