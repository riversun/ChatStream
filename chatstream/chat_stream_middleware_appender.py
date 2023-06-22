from fastapi import Request, Response
from fastapi.routing import APIRoute
from fastsession import FastSessionMiddleware, MemoryStore
from starlette.middleware.cors import CORSMiddleware

from .access_control.default_client_role_grant_middleware import DefaultClientRoleGrantMiddleware
from .default_api_names import DefaultApiNames
from .default_api_names_to_path import to_web_api_path


def append_middlewares(chat_stream, app, logger, eloc, opts=None, ):
    """
    ChatStreamに関連する Middleware を FastAPI アプリ に 追加する。
    """

    if opts is None:
        opts = {
            "fast_session": {
                "secret_key": "chatstream-default-session-secret-key",
                "store": MemoryStore(),
            },
            "develop_mode": False
        }

    app.add_middleware(DefaultClientRoleGrantMiddleware, chat_stream=chat_stream)

    logger.debug(eloc.to_str({
        "en": f"Middleware for granting default roles has been added.",
        "ja": f"デフォルトロール付与用ミドルウェア を追加しました。"}))

    app.add_middleware(FastSessionMiddleware,
                       secret_key="your-session-secret-key",  # Key for cookie signature
                       store=MemoryStore(),  # Store for session saving
                       http_only=True,  # True: Cookie cannot be accessed from client-side scripts such as JavaScript
                       secure=True if opts.get("develop_mode", False) else False,
                       skip_session_header={"header_name": "X-FastSession-Skip", "header_value": "skip"},
                       logger=chat_stream.logger
                       )

    logger.debug(eloc.to_str({
        "en": f"Middleware for HTTP sessions (FastSession) is added.",
        "ja": f"HTTPセッション用ミドルウェア(FastSession) を追加しました。"}))

    if opts.get("develop_mode", False) is True:
        logger.warning(eloc.to_str({
            "en": f"As a development mode, cookies used for HTTP sessions are allowed for both HTTPS and HTTP.",
            "ja": f"開発モードとして HTTPセッションに使用する Cookie を HTTPS と HTTP の双方で許可しています。"}))

    if opts.get("develop_mode", False) is True:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=[
                "X-ChatStream-API-DevTool-Enabled",  # UI側で開発ツール(DevTool) を有効にできるか否かを示すフラグ
                "X-ChatStream-Last-Generated-Message-Id",  # 直前に生成された最新メッセージのメッセージID
            ],
        )
        logger.warning(eloc.to_str({
            "en": f"CORS middleware has been added. As a development mode, all origins, methods, and headers are now acceptable. Please note that if you see this log in production, there is a security issue.",
            "ja": f"CORSミドルウェアを追加しました。開発モードとして、すべてのオリジン、メソッド、ヘッダが受け入れが可能となっています。プロダクションでこのログが表示された場合はセキュリティ上の問題がありますので注意してください。"}))
