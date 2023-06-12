import pytest

from chatstream.merge_dic import merge_dict


def test_merge_dict():
    src_dict = {"a": "val_a", "b": "val_b"}
    dest_dict = {"a": "val_a_dash", "b": None, "c": "val_c"}
    result = merge_dict(src_dict, dest_dict)

    # Check if the 'a' key has been overwritten
    assert result["a"] == "val_a_dash"

    # Check if the 'b' key has not been overwritten (since the new value is None)
    assert result["b"] == "val_b"

    # Check if the 'c' key has been added
    assert result["c"] == "val_c"

    # Check if 'dest_dict' is None, the function should return the original dictionary
    assert merge_dict(src_dict, None) == src_dict
