from typing import NamedTuple


class DefaultApiPaths(NamedTuple):
    """
    API エンドポイントパスを定義する 疑似定数クラス。
    各エンドポイントは Chat Stream サービスの一部であり、その役割は以下の通り。
    """

    GET_PROMPT = "/get_prompt"  # チャットモデルが次に生成するべきプロンプトを取得
    CHAT_STREAM = "/chat_stream"  # チャットストリーム API エンドポイント、ここでチャットを受信・送信する
    CLEAR_CONTEXT = "/clear_context"  # チャットモデルの現在のコンテキストをクリア
    GET_LOAD = "/get_load"  # チャットモデルの現在の負荷（処理中のチャット数）を取得
    SET_GENERATION_PARAMS = "/set_generation_params"  # チャットモデルの生成パラメータ（例：max_tokens）を設定
    GET_RESOURCE_USAGE = "/get_resource_usage"  # チャットモデルのリソース使用状況（CPU、メモリなど）を取得
    INDEX = "/"  # チャットモデルのWeb UI のパス
    JS = "/chatstream.js"  # チャットモデルの Web UI に必要なJavaScriptのパス
