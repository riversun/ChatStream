from typing import NamedTuple


class DefaultApiNames(NamedTuple):
    """
    API 名、API名一覧、API名に対するHTTPメソッド一覧　を定義する 定数クラス。（疑似定数クラス)

    """
    CHAT_STREAM = "chat_stream"  # チャットストリーム API エンドポイント、ここでチャットを受信・送信する
    CLEAR_CONTEXT = "clear_context"  # チャットモデルの現在のコンテキストをクリア
    GET_PROMPT = "get_prompt"  # チャットモデルが次に生成するべきプロンプトを取得
    SET_FEEDBACK = "set_feedback"  # チャット出力に関するユーザーフィードバックを受け付ける
    SET_GENERATION_PARAMS = "set_generation_params"  # チャットモデルの生成パラメータ（例：max_tokens）を設定
    GET_GENERATION_PARAMS = "get_generation_params"  # チャットモデルの生成パラメータ（例：max_tokens）を設定
    GET_LOAD = "get_load"  # チャットモデルの現在の負荷（処理中のチャット数）を取得
    GET_RESOURCE_USAGE = "get_resource_usage"  # チャットモデルのリソース使用状況（CPU、メモリなど）を取得

    WEBUI_INDEX = "webui_index"  # チャットモデルのWeb UI のパス
    WEBUI_JS = "webui_js"  # /chatstream.js"  # チャットモデルの Web UI に必要なJavaScriptのパス

    # API名一覧
    API_NAMES = [CHAT_STREAM, CLEAR_CONTEXT, GET_PROMPT, SET_GENERATION_PARAMS, GET_GENERATION_PARAMS, SET_FEEDBACK, GET_LOAD, GET_RESOURCE_USAGE, WEBUI_INDEX,
                 WEBUI_JS]
    # API名とHTTPメソッド一覧
    API_METHODS = {CHAT_STREAM: "POST",
                   CLEAR_CONTEXT: "POST",
                   GET_PROMPT: "GET",
                   SET_GENERATION_PARAMS: "POST",
                   GET_GENERATION_PARAMS: "GET",
                   SET_FEEDBACK: "POST",
                   GET_LOAD: "GET",
                   GET_RESOURCE_USAGE: "GET",
                   WEBUI_INDEX: "GET",
                   WEBUI_JS: "GET"}
    # TODO API名一覧にはAPIがすべて入ってる前提で、実装忘れ防止のために、API_METHOS に API_NAMESがすべて定義されているか最初にverifyするようにする
