import pytest
from chatstream.default_api_names import DefaultApiNames
from chatstream.default_api_names_to_path import to_web_api_path


def test_to_web_api_path():
    # 既知のAPI名とそれに対応するURLパス
    known_apis = {
        DefaultApiNames.CHAT_STREAM: "/chat_stream",
        DefaultApiNames.CLEAR_CONTEXT: "/clear_context",
        DefaultApiNames.GET_PROMPT: "/get_prompt",
        DefaultApiNames.SET_GENERATION_PARAMS: "/set_generation_params",
        DefaultApiNames.GET_GENERATION_PARAMS: "/get_generation_params",
        DefaultApiNames.GET_LOAD: "/get_load",
        DefaultApiNames.GET_RESOURCE_USAGE: "/get_resource_usage",
        DefaultApiNames.WEBUI_INDEX: "/",
        DefaultApiNames.WEBUI_JS: "/chatstream.js"
    }

    # 各既知のAPI名についてテスト
    for api_name, expected_path in known_apis.items():
        assert to_web_api_path(api_name) == expected_path, f"API名 '{api_name}' が期待したURLパスに変換されなかった"

    # 不明なAPI名でテスト
    with pytest.raises(Exception, match="Unknown API name"):
        to_web_api_path("unknown_api")
