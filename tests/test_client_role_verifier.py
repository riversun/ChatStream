from unittest.mock import Mock

import pytest
from fastsession import FastSessionMiddleware
from starlette.requests import Request

from chatstream import ChatStream
from chatstream.access_control.client_role_verifier import ClientRoleVerifier
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
async def test_verify_browser_client_default():
    # あるAPI名についてブラウザクライアントのデフォルトロールでのアクセスが許可されることを確認する

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http",
                                  "path": "/chat_stream",
                                  "headers": [
                                  ]}, receive=None)

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

    verifier = ClientRoleVerifier(chat_stream)

    verified_result = verifier.verify_client_role(test_request, "chat_stream")

    assert verified_result.get("success", False) is True


@pytest.mark.asyncio
async def test_verify_browser_client_default_with_invalid_api_name():
    # あるAPI名についてブラウザクライアントのデフォルトロールでのアクセスが許可されることを確認する

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http",
                                  "path": "/chat_stream",
                                  "headers": [
                                  ]}, receive=None)

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

    verifier = ClientRoleVerifier(chat_stream)
    verified_result = verifier.verify_client_role(test_request, "chat_stream1")
    assert verified_result.get("success") is False
    assert verified_result.get("message").startswith("Invalid api_name:'chat_stream1'.")


# TODO　昇格済の状態でUT追加


@pytest.mark.asyncio
async def test_verify_agent_client_sha256():
    #  エージェントクライアントの昇格済ロールが API アクセスできることを確認する

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http",
                                  "path": "/chat_stream",
                                  "headers": [
                                      (b"X-FastSession-Skip".lower(), b"skip"),
                                      (b"X-ChatStream-Auth-Header".lower(), b"change_your_pass"),
                                  ]}, receive=None)

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

    verifier = ClientRoleVerifier(chat_stream)

    verified_result = verifier.verify_client_role(test_request, "get_load")

    assert verified_result.get("success", False) == True


@pytest.mark.asyncio
async def test_invalid_api_name():
    # 不正なAPI 名を指定するとエラーとなることを確認する

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http",
                                  "path": "/chat_stream",
                                  "headers": [
                                      (b"X-FastSession-Skip".lower(), b"skip"),
                                      (b"X-ChatStream-Auth-Header".lower(), b"change_your_pass"),
                                  ]}, receive=None)

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

    verifier = ClientRoleVerifier(chat_stream)
    verify_result = verifier.verify_client_role(test_request, "get_load1")

    assert verify_result.get("success") is False
    assert verify_result.get("message").startswith("Invalid api_name:'get_load1'.")
