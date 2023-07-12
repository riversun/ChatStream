import hashlib


def hash_string(input_string):
    """
    文字列を SHA-256ハッシュ に変換する サンプルコード
    :param input_string:
    :return:
    """
    sha_signature = hashlib.sha256(input_string.encode()).hexdigest()
    return sha_signature


# 使用例
input_string = "change_your_pass"
hashed_string = hash_string(input_string)
print(f"hashed_string:'{hashed_string}'")
