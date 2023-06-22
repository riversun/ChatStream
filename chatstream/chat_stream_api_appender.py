from fastapi import Request, Response
from fastapi.routing import APIRoute

from .default_api_names import DefaultApiNames
from .default_api_names_to_path import to_web_api_path


def append_apis(chat_stream, app, opts, logger, eloc):
    """
    ChatStreamに関連するWeb APIをFastAPIアプリに追加する。

    chat_stream、app、optsを元に、特定のAPIを追加する。

    :param chat_stream: APIリクエストを処理するChatStreamオブジェクト。
    :param app: ルートを追加するFastAPIアプリケーション。
    :param dict opts: 追加するAPIを決定するためのオプションの辞書。キーとその意味は次の通り：

        "include": ホワイトリスト型指定、明示的に含めるAPI名のリスト。
        "exclude": ブラックリスト型指定、明示的に除外するAPI名のリスト。
        "all": すべてのAPIを含めるかどうかを決定するブール値。デフォルトはFalse。

        "web_ui_params": WebUI の初期化に使用するオプション

        以下のオプションは１つのみ指定可能
        "include", "exclude", "all"

    有効にするAPI名リスト（'include'または'exclude'に入れる）:
        "get_prompt": 有効にすると、現在のプロンプトを取得するAPIが追加される。
        "chat_stream": 有効にすると、チャットストリームリクエストを処理するAPIが追加される。
        "clear_context": 有効にすると、コンテキストをクリアするAPIが追加される。
        "get_load": 有効にすると、チャットストリームの現在の負荷を取得するAPIが追加される。
        "set_generation_params": 有効にすると、チャットストリームの生成パラメータを設定するAPIが追加される。
        "get_resource_usage": 有効にすると、CPUおよびGPUのリソース使用量（メモリ使用量）を取得するAPIが追加される。

    """

    # 以下のオプションは相互に排他的でなければならない
    mutually_exclusive_options = ["include", "exclude", "all"]

    # もし2つ以上のオプションが指定されていたらエラーを発生させる
    # （dict_key in opts ... dict_key が opts に存在するとき、dict_key のリストを返す）
    specified_options = [dict_key for dict_key in mutually_exclusive_options if dict_key in opts]
    if len(specified_options) > 1:
        # - "include","exclude","all" のうち2つ以上が指定されているとき
        # オプションは1つしか指定できないのでエラー
        raise ValueError(f"Only one option can be specified out of {mutually_exclusive_options}, but got {specified_options}")

    includes = opts.get("include", None)
    excludes = opts.get("exclude", None)
    is_all = opts.get("all", False)

    def is_enabled(api_name):
        """
        指定した API名が有効化否か
        :param api_name: 
        :return: 
        """

        is_valid_api_name = api_name in DefaultApiNames.API_NAMES
        if not is_valid_api_name:
            raise Exception(f"Invalid api name api_name:'{api_name}'")

        if includes is not None:
            return api_name in includes

        if excludes is not None:
            return not api_name in excludes

        if is_all:
            return True

        return False

    if is_enabled(DefaultApiNames.CHAT_STREAM):
        api_name = DefaultApiNames.CHAT_STREAM

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_chat_stream_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.GET_PROMPT):
        api_name = DefaultApiNames.GET_PROMPT

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_get_prompt_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.CLEAR_CONTEXT):
        api_name = DefaultApiNames.CLEAR_CONTEXT

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_clear_context_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.GET_LOAD):
        api_name = DefaultApiNames.GET_LOAD

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_get_load_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.SET_GENERATION_PARAMS):
        api_name = DefaultApiNames.SET_GENERATION_PARAMS

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_set_generation_params_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.SET_FEEDBACK):
        api_name = DefaultApiNames.SET_FEEDBACK

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_set_feedback_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added. method:{DefaultApiNames.API_METHODS.get(api_name)}",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました method:{DefaultApiNames.API_METHODS.get(api_name)}"}))

    if is_enabled(DefaultApiNames.GET_GENERATION_PARAMS):
        api_name = DefaultApiNames.GET_GENERATION_PARAMS

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_get_generation_params_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.GET_RESOURCE_USAGE):
        api_name = DefaultApiNames.GET_RESOURCE_USAGE

        async def api_func(request: Request, response: Response):
            return await chat_stream.handle_get_resource_usage_request(request)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.WEBUI_INDEX):
        ui_init_params = opts.get("web_ui_params", {})

        api_name = DefaultApiNames.WEBUI_INDEX

        async def api_func(request: Request, response: Response):
            return await chat_stream.index(request, response, opts={"ui_init_params": ui_init_params})

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))

    if is_enabled(DefaultApiNames.WEBUI_JS):
        api_name = DefaultApiNames.WEBUI_JS

        async def api_func(request: Request, response: Response):
            return await chat_stream.js(request, response)

        route = APIRoute(path=to_web_api_path(api_name), endpoint=api_func, methods=[DefaultApiNames.API_METHODS.get(api_name)])
        app.router.routes.append(route)
        logger.debug(eloc.to_str({"en": f"API endpoint '{route.path}' added.",
                                  "ja": f"APIエンドポイント '{route.path}' を追加しました"}))
