import pytest

from chatstream.easy_locale import EasyLocale


def test_easy_locale():
    """
    簡易ロケールをテストする
    :return:
    """
    obj = EasyLocale({'fallbackLocale': 'en'})
    greeting_message = {"ja": "こんにちは", "en": "Hello"}
    assert obj.to_str(greeting_message) in ["こんにちは", "Hello"]

    obj = EasyLocale({'fallbackLocale': 'en', 'locale': 'en'})
    greeting_message = {"ja": "こんにちは", "en": "Hello"}
    assert obj.to_str(greeting_message) == "Hello"

    obj = EasyLocale({'fallbackLocale': 'en', 'locale': 'en-US'})
    greeting_message = {"ja": "こんにちは", "en": "Hello"}
    assert obj.to_str(greeting_message) == "Hello"

    obj = EasyLocale({'fallbackLocale': 'en', 'locale': 'ja-JP'})
    greeting_message = {"ja": "こんにちは", "en": "Hello"}
    assert obj.to_str(greeting_message) == "こんにちは"

    assert obj.to_str('おはよう') == 'おはよう'
    obj = EasyLocale({'locale': None})
    assert obj.to_str({"ja": "こんにちは", "en": "Hello"}) in ["こんにちは", "Hello"]
