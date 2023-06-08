from fastapi import Request, Response
from fastapi.routing import APIRoute

from .default_api_paths import DefaultApiPaths

def append_apis(chat_stream, app, opts,logger):

    """
    ChatStreamに関連するWeb APIをFastAPIアプリに追加する。

    chat_stream、app、optsを元に、特定のAPIを追加する。
    各APIは、そのキーが'include'リストに含まれている、
    'exclude'リストに含まれていない、または'all_apis'がTrueに設定されている場合に有効/無効を切り替えることができる。

    :param chat_stream: APIリクエストを処理するChatStreamオブジェクト。
    :param app: ルートを追加するFastAPIアプリケーション。
    :param dict opts: 追加するAPIを決定するためのオプションの辞書。キーとその意味は次の通り：
        "include": ホワイトリスト型指定、明示的に含めるAPI名のリスト。
        "exclude": ブラックリスト型指定、明示的に除外するAPI名のリスト。
        "all_apis": すべてのAPIを含めるかどうかを決定するブール値。デフォルトはFalse。
        "web_ui_params": WebUI の初期化に使用するオプション

    有効にするAPI名リスト（'include'または'exclude'に入れる）:
        "get_prompt": 有効にすると、現在のプロンプトを取得するAPIが追加される。
        "chat_stream": 有効にすると、チャットストリームリクエストを処理するAPIが追加される。
        "clear_context": 有効にすると、コンテキストをクリアするAPIが追加される。
        "get_load": 有効にすると、チャットストリームの現在の負荷を取得するAPIが追加される。
        "set_generation_params": 有効にすると、チャットストリームの生成パラメータを設定するAPIが追加される。
        "get_resource_usage": 有効にすると、CPUおよびGPUのリソース使用量（メモリ使用量）を取得するAPIが追加される。
        "web_ui": 有効にすると、チャットストリームのWeb UIが追加される。


    """
    includes = opts.get("include", [])
    excludes = opts.get("exclude", [])
    is_all = opts.get("all_apis", False)

    def is_enabled(key):
        _ret = (not key in excludes) and (key in includes or is_all)
        return _ret

    if is_enabled("chat_stream"):
        async def chat_stream_api(request: Request):
            return await chat_stream.handle_chat_stream_request(request)

        app.router.routes.append(
            APIRoute(path=DefaultApiPaths.CHAT_STREAM, endpoint=chat_stream_api, methods=["POST"]))

        logger.debug(f"APIエンドポイント '{DefaultApiPaths.CHAT_STREAM}' を追加しました")

    if is_enabled("get_prompt"):
        async def get_prompt_api(request: Request):
            return await chat_stream.handle_get_prompt_request(request)

        app.router.routes.append(
            APIRoute(path=DefaultApiPaths.GET_PROMPT, endpoint=get_prompt_api, methods=["GET"]))

        if chat_stream.allow_get_prompt:
            logger.debug(f"APIエンドポイント '{DefaultApiPaths.GET_PROMPT}' を追加しました")
        else:
            logger.warning(
                f"APIエンドポイント '{DefaultApiPaths.GET_PROMPT}' を追加しましたが、このAPIは無効です。有効にするには、allow_get_prompt=True で ChatStream を初期化する必要があります")

    if is_enabled("clear_context"):
        async def clear_context_api(request: Request):
            return await chat_stream.handle_clear_context_request(request)

        app.router.routes.append(
            APIRoute(path=DefaultApiPaths.CLEAR_CONTEXT, endpoint=clear_context_api, methods=["POST"]))

        if chat_stream.allow_clear_context:
            logger.debug(f"APIエンドポイント '{DefaultApiPaths.CLEAR_CONTEXT}' を追加しました")
        else:
            logger.warning(
                f"APIエンドポイント '{DefaultApiPaths.CLEAR_CONTEXT}' を追加しましたが、このAPIは無効です。有効にするには、allow_clear_context=True で ChatStream を初期化する必要があります")

    if is_enabled("get_load"):
        async def get_load_api(request: Request):
            return await chat_stream.handle_get_load_request(request)

        app.router.routes.append(APIRoute(path=DefaultApiPaths.GET_LOAD, endpoint=get_load_api, methods=["GET"]))

        if chat_stream.allow_get_load:
            logger.debug(f"APIエンドポイント '{DefaultApiPaths.GET_LOAD}' を追加しました")
        else:
            logger.warning(
                f"APIエンドポイント '{DefaultApiPaths.GET_LOAD}' を追加しましたが、このAPIは無効です。有効にするには、allow_get_load=True で ChatStream を初期化する必要があります")

    if is_enabled("set_generation_params"):
        async def set_generation_params_api(request: Request):
            return await chat_stream.handle_set_generation_params_request(request)

        app.router.routes.append(
            APIRoute(path=DefaultApiPaths.SET_GENERATION_PARAMS, endpoint=set_generation_params_api,
                     methods=["POST"]))

        if chat_stream.allow_set_generation_params:
            logger.debug(f"APIエンドポイント '{DefaultApiPaths.SET_GENERATION_PARAMS}' を追加しました")
        else:
            logger.warning(
                f"APIエンドポイント '{DefaultApiPaths.SET_GENERATION_PARAMS}' を追加しましたが、このAPIは無効です。有効にするには、allow_set_generation_params=True で ChatStream を初期化する必要があります")

    if is_enabled("get_resource_usage"):
        async def get_resource_usage_api(request: Request):
            return await chat_stream.handle_get_resource_usage_request(request)

        app.router.routes.append(
            APIRoute(path=DefaultApiPaths.GET_RESOURCE_USAGE, endpoint=get_resource_usage_api, methods=["GET"]))

        if chat_stream.allow_get_resource_usage:
            logger.debug(f"APIエンドポイント '{DefaultApiPaths.GET_RESOURCE_USAGE}' を追加しました")
        else:
            logger.warning(
                f"APIエンドポイント '{DefaultApiPaths.GET_RESOURCE_USAGE}' を追加しましたが、このAPIは無効です。有効にするには、allow_get_resource_usage=True で ChatStream を初期化する必要があります")

    if is_enabled("web_ui"):
        ui_init_params = opts.get("web_ui_params", {})

        async def js(response: Response):
            return await chat_stream.js(response)

        app.router.routes.append(APIRoute(path=DefaultApiPaths.JS, endpoint=js, methods=["GET"]))

        if chat_stream.allow_web_ui:
            logger.debug(f"APIエンドポイント '{DefaultApiPaths.JS}' を追加しました")
        else:
            logger.warning(
                f"APIエンドポイント '{DefaultApiPaths.JS}' を追加しましたが、このAPIは無効です。有効にするには、allow_web_ui=True で ChatStream を初期化する必要があります")

        async def index(request: Request, response: Response):
            return await chat_stream.index(response, opts={"ui_init_params": ui_init_params})

        app.router.routes.append(APIRoute(path=DefaultApiPaths.INDEX, endpoint=index, methods=["GET"]))

        if chat_stream.allow_web_ui:
            logger.debug(f"APIエンドポイント '{DefaultApiPaths.INDEX}' を追加しました")
        else:
            logger.warning(
                f"APIエンドポイント '{DefaultApiPaths.INDEX}' を追加しましたが、このAPIは無効です。有効にするには、allow_web_ui=True で ChatStream を初期化する必要があります")
