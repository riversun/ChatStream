from unittest.mock import Mock

import pytest
from fastsession import FastSessionMiddleware, MemoryStore

from starlette.requests import Request

from chatstream.access_control.client_role_authorizer_for_agent import ClientRoleAuthorizerForAgent
from chatstream.access_control.client_role_wrapper import ClientRoleWrapper
from chatstream.access_control.default_client_role_grant_middleware import CHAT_STREAM_CLIENT_ROLE
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
            "allow": ["chat_stream", "clear_context", "web_ui"],
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
async def test_get_promoted_role_of_header_phrase():
    # リクエストヘッダ "X-ChatStream-Auth-Header":"i am server" を指定すると、これに対応したロールが戻る

    logger = ConsoleLogger()
    eloc = EasyLocale()

    # インスタンスを生成
    wrapper = ClientRoleWrapper(logger, eloc, client_roles)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http",
                                  "headers": [
                                      (b"X-FastSession-Skip".lower(), b"skip"),
                                      (b"X-ChatStream-Auth-Header".lower(), b"i am server"),
                                  ],
                                  }, receive=None)

    app = Mock()

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

    client_role_auth_for_agent = ClientRoleAuthorizerForAgent(logger, eloc, client_role_wrapper=wrapper)

    role = client_role_auth_for_agent.get_promoted_role(test_request)
    role_name = role[0]
    role_contents = role[1]

    assert role_name == "server_admin"
    assert role_contents == {'apis': {'allow': 'all', 'auth_method': 'header_phrase', 'header_phrase': 'i am server', 'use_session': False}}


@pytest.mark.asyncio
async def test_get_promoted_role_of_header_phrase_sha256():
    # リクエストヘッダ "X-ChatStream-Auth-Header":"change_your_pass" を指定すると、SHA256 でマッチしてこれに対応したロールが戻る

    logger = ConsoleLogger()
    eloc = EasyLocale()

    # インスタンスを生成
    wrapper = ClientRoleWrapper(logger, eloc, client_roles)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http",
                                  "headers": [
                                      (b"X-FastSession-Skip".lower(), b"skip"),
                                      (b"X-ChatStream-Auth-Header".lower(), b"change_your_pass"),
                                  ],
                                  }, receive=None)

    app = Mock()

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

    client_role_auth_for_agent = ClientRoleAuthorizerForAgent(logger, eloc, client_role_wrapper=wrapper)

    role = client_role_auth_for_agent.get_promoted_role(test_request)
    role_name = role[0]
    role_contents = role[1]

    assert role_name == "server_admin_sha"
    assert role_contents == {
        'apis': {'allow': 'all', 'auth_method': 'header_phrase_sha256', 'header_phrase': '597d7fb99ab9ce00b59918f425031c296371e1af9848071c156be7e54916d84c',
                 'use_session': False}}
