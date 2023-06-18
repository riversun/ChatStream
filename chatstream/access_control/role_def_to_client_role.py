def role_def_to_client_role(role_def):
    """
    ロール定義(role_def)から client_role オブジェクトに変換する
    :param role_def:
    :return:
    """

    role_name = role_def[0]
    role_contents = role_def[1]
    apis = role_contents.get("apis")
    allow = apis.get("allow")
    auth_method = apis.get("auth_method")
    use_session = apis.get("use_session", False)
    enable_dev_tool = apis.get("enable_dev_tool", False)

    client_role={}
    client_role["client_role_name"] = role_name
    client_role["allowed_apis"] = allow
    client_role["enable_dev_tool"] = enable_dev_tool

    return client_role