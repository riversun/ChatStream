from unittest.mock import Mock

import pytest
from fastsession import FastSessionMiddleware
from starlette.requests import Request

from chatstream import ChatStream
from chatstream.access_control.client_role_authorizer_for_browser import ClientRoleAuthorizerForBrowser
from chatstream.access_control.default_client_role_grant_middleware import DefaultClientRoleGrantMiddleware
from chatstream.easy_locale import EasyLocale


class ConsoleLogger:
    def info(self, str):
        print(f"[INFO ]{str}")
        pass

    def debug(self, str):
        print(f"[DEBUG]{str}")
        pass


# ロールのデータ
client_roles = {
    "user": {
        "apis": {
            "allow": ["chat_stream", "clear_context"],
            "auth_method": "nothing",
            "use_session": True,  # セッションベースの認証
        }
    },
    "developer": {
        "apis": {
            "allow": ["chat_stream",
                      "clear_context",

                      "get_prompt",
                      "set_generation_params",
                      ],
            "auth_method": "ui_pass_phrase",
            "ui_pass_phrase": "dev mode",
            "use_session": True,
            "enable_dev_tool": True,

        },
    },
    "admin": {
        "apis": {
            "allow": "all",
            "auth_method": "ui_pass_phrase",
            "ui_pass_phrase": "admin mode",
            "use_session": True,
            "enable_dev_tool": True,
        },
    },
    "admin_sha": {
        "apis": {
            "allow": "all",
            "auth_method": "ui_pass_phrase_sha256",
            "ui_pass_phrase_sha256": "597d7fb99ab9ce00b59918f425031c296371e1af9848071c156be7e54916d84c",
            "use_session": True,
            "enable_dev_tool": True,
        },
    },
    "server_default": {
        "apis": {
            "allow": ["get_load"],
            "auth_method": "nothing",
            "use_session": False,  # サーバーの場合はセッション使わない
        },
    },
    "server_admin": {
        "apis": {
            "allow": "all",
            "auth_method": "header_phrase",
            "header_phrase": "i am server",
            "use_session": False,  # サーバーの場合はセッション使わない
        },
    },
    "server_admin_sha": {
        "apis": {
            "allow": "all",
            "auth_method": "header_phrase_sha256",
            "header_phrase": "597d7fb99ab9ce00b59918f425031c296371e1af9848071c156be7e54916d84c",  # change_your_pass
            "use_session": False,  # サーバーの場合はセッション使わない
        },
    }
}


@pytest.mark.asyncio
async def test_promote_by_user_input_algo_ui_pass_phrase():
    # ブラウザクライアントの user_input でロールが昇格する

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http", "path": "/chat_stream", "headers": [(b"x-ignore-header", b"ignore-value")]}, receive=None)

    session_middleware = FastSessionMiddleware(
        app=app,
        secret_key="test",
        skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"},
        logger=logger
    )

    class MockResponse:
        def __init__(self):
            self.headers = {}

    emulated_response = MockResponse()

    async def call_next(request):
        return emulated_response

    await session_middleware.dispatch(test_request, call_next)

    await default_client_role_middleware.dispatch(test_request, call_next)

    wrapper = chat_stream.client_role_wrapper
    client_role_auth_for_browser = ClientRoleAuthorizerForBrowser(logger, eloc, client_role_wrapper=wrapper)
    role = client_role_auth_for_browser.get_promoted_role(test_request, "dev mode")

    assert role.get("client_role_name") == "developer"
    assert role.get("allowed_apis") == ['chat_stream', 'clear_context', 'get_prompt', 'set_generation_params']
    assert role.get("enable_dev_tool") == True


@pytest.mark.asyncio
async def test_promote_by_user_input_algo_ui_pass_phrase_fail():
    # ブラウザクライアントの user_input で間違えた値の場合はNone

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http", "path": "/chat_stream", "headers": [(b"x-ignore-header", b"ignore-value")]}, receive=None)

    session_middleware = FastSessionMiddleware(
        app=app,
        secret_key="test",
        skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"},
        logger=logger
    )

    class MockResponse:
        def __init__(self):
            self.headers = {}

    emulated_response = MockResponse()

    async def call_next(request):
        return emulated_response

    await session_middleware.dispatch(test_request, call_next)

    await default_client_role_middleware.dispatch(test_request, call_next)

    wrapper = chat_stream.client_role_wrapper
    client_role_auth_for_browser = ClientRoleAuthorizerForBrowser(logger, eloc, client_role_wrapper=wrapper)
    role = client_role_auth_for_browser.get_promoted_role(test_request, "dev mode11")
    assert role is None


@pytest.mark.asyncio
async def test_promote_by_user_input_algo_ui_pass_phrase_sha256():
    # ブラウザクライアントの user_input でロールが昇格する

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http", "path": "/chat_stream", "headers": [(b"x-ignore-header", b"ignore-value")]}, receive=None)

    session_middleware = FastSessionMiddleware(
        app=app,
        secret_key="test",
        skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"},
        logger=logger
    )

    class MockResponse:
        def __init__(self):
            self.headers = {}

    emulated_response = MockResponse()

    async def call_next(request):
        return emulated_response

    await session_middleware.dispatch(test_request, call_next)

    await default_client_role_middleware.dispatch(test_request, call_next)

    wrapper = chat_stream.client_role_wrapper
    client_role_auth_for_browser = ClientRoleAuthorizerForBrowser(logger, eloc, client_role_wrapper=wrapper)
    role = client_role_auth_for_browser.get_promoted_role(test_request, "change_your_pass")

    assert role.get("client_role_name") == "admin_sha"
    assert role.get("allowed_apis") == "all"
    assert role.get("enable_dev_tool") is True
