def merge_dict(src_dict, dest_dict):
    """
    dictSrc に dictDest にある各パラメータを上書きする
    ただし dictDest にあるパラメータ値が None の場合は反映しない

    :param src_dict:
    :param dest_dict:
    :return:
    """

    dictSrcCopy = src_dict.copy()
    # dictSrc に、 dictDest を上書きする。
    # ただし、 dictDest のキーに対する値が None なら上書きしない
    # None の場合はセットしない
    if dest_dict is not None:
        for key, value in dest_dict.items():
            if key in dictSrcCopy and value is not None:
                dictSrcCopy[key] = value
            elif value is not None:
                dictSrcCopy[key] = value

    else:
        return src_dict

    return dictSrcCopy


if False:
    r = merge_dict({"a": "val_a", "b": "val_b"}, {"a": "val_a_dash", "b": None, "c": "val_c"})
    print(r)
