from unittest.mock import Mock

import pytest
from fastsession import FastSessionMiddleware, MemoryStore

from starlette.requests import Request

from chatstream import ChatStream
from chatstream.access_control.client_role_wrapper import ClientRoleWrapper
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
async def test_handling_browser_client_role_access():
    # ブラウザからアクセスされたとき、
    # ブラウザ用デフォルトロールが セッションに(一旦)セットされることを確認する

    # ブラウザ用ロールはセッションに一旦保存される理由
    # ブラウザ用ロールがセッションに一旦保存される理由は、ブラウザ（つまり人間ユーザー）からのリクエストの場合
    # 途中、チャット画面で特殊文字列（パスフレーズ）を入力することで権限を昇格させる(やっていることは高度な権限をもつロールに変更しているということになる）
    # ことができる。
    #
    # このとき、昇格を担うのは "chat_stream" API　だが、昇格した状態で "get_load" など、高度な権限を持たないとアクセスできない
    # APIにアクセスしにいく。そのため、パスを横断（つまり request 横断）でロールを保持しなければならないため、
    # ブラウザアクセスの場合は　request.state ではなくセッション側にロール情報をもつ。

    # そして、別の API にアクセスするタイミングで
    # セッションから request.state にロール情報を付与するようにする。
    #
    # そのように考えると、エージェントからのアクセスの場合はヘッダで認証するため、 client_role_grant_middlewareで最終的なロールを付与することも可能だが、
    # ソフトウェア構造上、処理の見通しのよさのため、
    # ・client_role_grant_middleware はデフォルトのロールを付与する役割、
    # ・各ＡＰＩ前で実行される authorizer_handler （仮称）は、最終的なロールを付与する役割　
    # と役割を分割したので、そのように実装している

    logger = ConsoleLogger()

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
    session = wrapper.get_browser_session(test_request)
    client_role_in_session = session.get("chat_stream_client_role", None)

    assert client_role_in_session.get("client_role_name") == "user"
    assert client_role_in_session.get("allowed_apis") == ['chat_stream', 'clear_context', 'web_ui']
    assert client_role_in_session.get("enable_dev_tool") == False


@pytest.mark.asyncio
async def test_handling_agent_client_role_access():
    # エージェントからアクセスされたとき、
    # エージェント用のデフォルトロールが request にセットされることを確認する

    logger = ConsoleLogger()

    app = Mock()

    chat_stream = ChatStream(logger=logger, client_roles=client_roles)

    default_client_role_middleware = DefaultClientRoleGrantMiddleware(app, chat_stream=chat_stream)

    # テスト用リクエストを作成
    # 自前で Request を new するときは、リクエストヘッダはタプルで指定する
    test_request = Request(scope={"type": "http", "path": "/chat_stream", "headers": [(b"X-FastSession-Skip".lower(), b"skip".lower())]}, receive=None)

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

    role = wrapper.get_agent_current_client_role(test_request)
    assert role.get("client_role_name") == "server_default"
    assert role.get("allowed_apis") == ['get_load']
