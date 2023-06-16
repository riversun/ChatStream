from unittest.mock import Mock

import pytest
from fastsession import FastSessionMiddleware, MemoryStore

from starlette.requests import Request

from chatstream.access_control.client_role_wrapper import ClientRoleWrapper
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

    assert browser_role['client_role_name'] == 'user'
    assert browser_role['allowed_apis'] == ['chat_stream', 'clear_context', 'web_ui']
    assert browser_role['enable_dev_tool'] == False

    # エージェントクライアント用のデフォルトロールを取得
    agent_role = wrapper.get_agent_default_client_role()
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
    key = "client_role_name"
    value = "test_role"
    wrapper.set_request_state(test_request, key, value)
    role2 = wrapper.get_agent_current_client_role(test_request)
    assert role2 == "test_role"
