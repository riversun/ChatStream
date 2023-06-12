def merge_dict(src_dict, dest_dict):
    """
    Overwrites parameters of `src_dict` with those in `dest_dict`.
    However, if the value of the parameter in `dest_dict` is None, it is not reflected.

    :param src_dict: The original dictionary.
    :param dest_dict: The dictionary whose values will be used to overwrite the original.
    :return: A new dictionary that results from merging the two input dictionaries.
    """

    src_dict_copy = src_dict.copy()

    if dest_dict is not None:
        for key, value in dest_dict.items():
            if key in src_dict_copy and value is not None:
                src_dict_copy[key] = value
            elif value is not None:
                src_dict_copy[key] = value

    else:
        return src_dict

    return src_dict_copy
