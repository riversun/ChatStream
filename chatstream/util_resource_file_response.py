import importlib.resources as pkg_resources

from fastapi import Response


def _send_resource(file_name, response: Response, replacer=None):
    """
    パッケージリソースからテキストデータを読み込み、FastAPIのレスポンスに設定する。

    :param file_name: リソースファイルの名称。ファイルはパッケージ内の"data"ディレクトリに存在することを想定。
    :type file_name: str
    :param response: FastAPIのレスポンスオブジェクト。レスポンスのbody, media_type, status_codeが更新される。
    :type response: fastapi.Response
    :param replacer: データの置換を行う関数。Noneでなければ、読み込んだデータに対して呼び出される。
    :type replacer: callable, optional
    :returns: 更新されたレスポンスオブジェクト。
    :rtype: fastapi.Response
    :raises: リソースの読み込みやデータの置換でエラーが発生した場合、そのエラーは上げられる。
    """
    data = pkg_resources.read_text(f"{__package__}.data", file_name)
    if replacer:
        data = replacer(data)

    response.body = data.encode("utf-8")  # You need to encode string to bytes
    response.media_type = "text/html"
    response.status_code = 200  # Add this line

    return response
