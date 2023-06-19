from unittest.mock import Mock

import pytest
from fastsession import FastSessionMiddleware, MemoryStore

from starlette.requests import Request

from chatstream import ChatStream
from chatstream.access_control.client_role_authorizer_for_agent import ClientRoleAuthorizerForAgent
from chatstream.access_control.client_role_finalizer import ClientRoleFinalizer
from chatstream.access_control.client_role_wrapper import ClientRoleWrapper
from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE, DefaultClientRoleGrantMiddleware
from chatstream.easy_locale import EasyLocale


class ConsoleLogger:
    def info(self, str):
        print(f"[INFO ]{str}")
        pass

    def debug(self, str):
        print(f"[DEBUG]{str}")
        pass


from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE

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
                      "web_ui",
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
async def test_set_final_role_when_browser_default_client_accessed():
    # セッションにひもづいた、ブラウザクライアントのデフォルトロールが request.state 下にセットされることを確認する

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

    role_finalizer = ClientRoleFinalizer(logger, eloc, client_role_wrapper=wrapper)

    session = wrapper.get_browser_session(test_request)
    client_role_in_session = session.get(CHAT_STREAM_CLIENT_ROLE, None)

    assert client_role_in_session.get("client_role_name") == "user"
    assert client_role_in_session.get("allowed_apis") == ['chat_stream', 'clear_context']

    role_finalizer.set_final_role(test_request)

    client_role_in_request_state = wrapper.get_request_state(test_request, CHAT_STREAM_CLIENT_ROLE, None)

    # request.state 以下にセッションに格納されている client_role が入ってることを確認する
    assert client_role_in_request_state.get("client_role_name") == "user"
    assert client_role_in_request_state.get("allowed_apis") == ['chat_stream', 'clear_context']


@pytest.mark.asyncio
async def test_set_final_role_when_agent_default_client_accessed():
    # セッションにひもづいた、エージェントクライアントのデフォルトロールが request.state 下にセットされることを確認する

    logger = ConsoleLogger()
    eloc = EasyLocale()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http", "path": "/chat_stream", "headers": [(b"X-FastSession-Skip".lower(), b"skip")]}, receive=None)

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

    role_finalizer = ClientRoleFinalizer(logger, eloc, client_role_wrapper=wrapper)
    role_finalizer.set_final_role(test_request)

    client_role_in_request_state = wrapper.get_request_state(test_request, CHAT_STREAM_CLIENT_ROLE, None)
    print(client_role_in_request_state)
    assert client_role_in_request_state.get("client_role_name") == "server_default"
    assert client_role_in_request_state.get("allowed_apis") == ['get_load']


@pytest.mark.asyncio
async def test_set_final_role_when_agent_client_accessed_with_promoted_role():
    # セッションにひもづいた、エージェントクライアントの昇格済ロールが request.state 下にセットされることを確認する

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
                                      (b"X-ChatStream-Auth-Header".lower(), b"i am server"),
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

    wrapper = chat_stream.client_role_wrapper

    role_finalizer = ClientRoleFinalizer(logger, eloc, client_role_wrapper=wrapper)
    role_finalizer.set_final_role(test_request)

    client_role_in_request_state = wrapper.get_request_state(test_request, CHAT_STREAM_CLIENT_ROLE, None)
    # 昇格したロールであることを確認する
    assert client_role_in_request_state.get("client_role_name") == "server_admin"
    assert client_role_in_request_state.get("allowed_apis") == "all"


@pytest.mark.asyncio
async def test_set_final_role_when_agent_client_accessed_with_promoted_role_sha256():
    # セッションにひもづいた、エージェントクライアントの昇格済ロールが request.state 下にセットされることを確認する(sha256版)

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

    wrapper = chat_stream.client_role_wrapper

    role_finalizer = ClientRoleFinalizer(logger, eloc, client_role_wrapper=wrapper)
    role_finalizer.set_final_role(test_request)

    client_role_in_request_state = wrapper.get_request_state(test_request, CHAT_STREAM_CLIENT_ROLE, None)
    print(client_role_in_request_state)
    # 昇格したロールであることを確認する
    assert client_role_in_request_state.get("client_role_name") == "server_admin_sha"
    assert client_role_in_request_state.get("allowed_apis") == "all"

# TODO ブラウザで、デフォルトロールではなく途中で昇格した場合認証済の場合のUT
