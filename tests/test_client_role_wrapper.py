from unittest.mock import Mock

import pytest
from fastsession import FastSessionMiddleware, MemoryStore

from starlette.requests import Request

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
async def test_client_role_wrapper():
    # ロガーとロケーションはテスト用にダミーを設定

    logger = ConsoleLogger()
    eloc = EasyLocale()

    # インスタンスを生成
    wrapper = ClientRoleWrapper(logger, eloc, client_roles)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http", "headers": [(b"x-ignore-header", b"ignore-value")]}, receive=None)

    app = Mock()  # モックのASGIアプリケーションを作成します

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
    print(test_request.state)
    # test_request.state.__chatstream__ = {"client_role_name": "user"}

    # ロールベースのアクセスコントロールが使用されていることを確認
    # (client_rolesがコンストラクタで指定されていればそうなる)
    assert wrapper.is_use_client_role_based_access_control()

    # このリクエストがブラウザクライアントアクセスであることを判断
    assert wrapper.is_browser_client_access(test_request)

    # エージェントクライアントアクセスではないことを判断
    assert not wrapper.is_agent_client_access(test_request)

    # ブラウザクライアント用のデフォルトロールを取得
    browser_role = wrapper.get_browser_default_client_role()
    assert browser_role['enabled'] == True
    assert browser_role['client_role_name'] == 'user'
    assert browser_role['allowed_apis'] == ['chat_stream', 'clear_context', 'web_ui']
    assert browser_role['enable_dev_tool'] == False

    # エージェントクライアント用のデフォルトロールを取得
    agent_role = wrapper.get_agent_default_client_role()
    assert agent_role['enabled'] == True
    assert agent_role['client_role_name'] == 'server_default'
    assert agent_role['allowed_apis'] == ['get_load']
    assert agent_role['enable_dev_tool'] == False
    # print(agent_role)

    # セッションがあるとき、セッションを取得できる
    session = wrapper.get_browser_session(test_request)

    assert session["__cause__"] == "new"

    role = wrapper.get_agent_current_client_role(test_request)
    assert role is None  # まだ、 request.state以下にロールは定義されていないのでNone

    # 自前で set_request_state をよび、ロールをセットする

    # ChatStream 用の request.state にキー、値を書き込む
    key = CHAT_STREAM_CLIENT_ROLE
    value = {"client_role_name": "example_role", "allowed_apis": ["example1", "example2"]}
    wrapper.set_request_state(test_request, key, value)
    role2 = wrapper.get_agent_current_client_role(test_request)
    assert role2.get("client_role_name") == "example_role"


def test_verify_success():
    # 正常系のテストケース
    client_roles = {
        "user": {
            "apis": {
                "allow": ["chat_stream", "clear_context"],
                "auth_method": "nothing",
                "use_session": True,
            }
        },
    }
    logger = ConsoleLogger()
    eloc = EasyLocale()
    wrapper = ClientRoleWrapper(logger, eloc, client_roles=client_roles)
    assert wrapper.verify() == True


def test_verify_invalid_allow():
    # allow に不正な値が含まれているケース
    client_roles = {
        "user": {
            "apis": {
                "allow": ["invalid_api_name"],
                "auth_method": "nothing",
                "use_session": True,
            }
        },
    }
    logger = ConsoleLogger()
    eloc = EasyLocale()
    wrapper = ClientRoleWrapper(logger, eloc, client_roles=client_roles)

    with pytest.raises(ValueError):
        wrapper.verify()


def test_verify_no_default_role():
    # ブラウザ用デフォルトロールが存在しないケース
    client_roles = {
        "user": {
            "apis": {
                "allow": ["chat_stream", "clear_context", "web_ui"],
                "auth_method": "some_method",
                "use_session": True,
            }
        },
    }
    logger = ConsoleLogger()
    eloc = EasyLocale()
    wrapper = ClientRoleWrapper(logger, eloc, client_roles=client_roles)

    with pytest.raises(Exception):
        wrapper.verify()


def test_verify_multiple_default_roles():
    # デフォルトロールが複数存在するケース
    client_roles = {
        "user": {
            "apis": {
                "allow": ["chat_stream", "clear_context", "web_ui"],
                "auth_method": "nothing",
                "use_session": True,
            }
        },
        "user2": {
            "apis": {
                "allow": ["chat_stream", "clear_context", "web_ui"],
                "auth_method": "nothing",
                "use_session": True,
            }
        },
    }
    logger = ConsoleLogger()
    eloc = EasyLocale()
    wrapper = ClientRoleWrapper(logger, eloc, client_roles=client_roles)

    with pytest.raises(Exception):
        wrapper.verify()


def test_verify_default_role_no_session():
    client_roles = {
        "user": {
            "apis": {
                "allow": ["chat_stream", "clear_context"],
                "auth_method": "nothing",
                "use_session": True,  # セッションベースの認証を使用する = Browser用
            }
        },
        "agent": {
            "apis": {
                "allow": ["chat_stream", "clear_context"],
                "auth_method": "something",
                "use_session": False,  # セッションベースの認証を使用しない = Agent用
            }
        },
    }
    logger = ConsoleLogger()
    eloc = EasyLocale()
    wrapper = ClientRoleWrapper(logger, eloc, client_roles=client_roles)
    wrapper.verify()

    assert wrapper.verify() == True


@pytest.mark.asyncio
async def test_get_agent_special_roles():
    logger = ConsoleLogger()
    eloc = EasyLocale()

    # インスタンスを生成
    wrapper = ClientRoleWrapper(logger, eloc, client_roles)

    agent_roles = wrapper.get_agent_special_role_defs()

    assert agent_roles == [('server_admin'
                            , {'apis': {'allow': 'all', 'auth_method': 'header_phrase', 'header_phrase': 'i am server', 'use_session': False}}),
                           ('server_admin_sha',
                            {'apis': {'allow': 'all', 'auth_method': 'header_phrase_sha256',
                                      'header_phrase': '597d7fb99ab9ce00b59918f425031c296371e1af9848071c156be7e54916d84c', 'use_session': False}})]


@pytest.mark.asyncio
async def test_get_browser_special_roles():
    logger = ConsoleLogger()
    eloc = EasyLocale()

    # インスタンスを生成
    wrapper = ClientRoleWrapper(logger, eloc, client_roles)

    browser_roles = wrapper.get_browser_special_role_defs()
    assert browser_roles == [('developer',
                              {'apis':
                                   {'allow': ['chat_stream', 'clear_context', 'web_ui', 'get_prompt', 'set_generation_params'], 'auth_method': 'ui_pass_phrase',
                                    'ui_pass_phrase': 'dev mode', 'use_session': True, 'enable_dev_tool': True}}),
                             ('admin',
                              {'apis':
                                   {'allow': 'all', 'auth_method': 'ui_pass_phrase', 'ui_pass_phrase': 'admin mode', 'use_session': True}})]
