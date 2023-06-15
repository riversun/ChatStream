from chatstream.default_api_names import DefaultApiNames


def test_all_api_methods_defined():
    # API_NAMESにあるすべてのAPIがAPI_METHODSに定義されているか確認
    for api_name in DefaultApiNames.API_NAMES:
        assert api_name in DefaultApiNames.API_METHODS, f"APIメソッド '{api_name}' が API_METHODS に見つからない"
