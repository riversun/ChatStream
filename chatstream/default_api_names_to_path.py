from chatstream.default_api_names import DefaultApiNames


def to_web_api_path(api_name):
    """
    api_name を実際の urlパスに変換する
    :param api_name:
    :return:
    """
    if api_name not in DefaultApiNames.API_NAMES:
        raise Exception(f"Unknown API name:'{api_name}'")

    if api_name == DefaultApiNames.WEBUI_INDEX:
        return "/"
    elif api_name == DefaultApiNames.WEBUI_JS:
        return "/chatstream.js"
    else:
        return "/" + api_name
