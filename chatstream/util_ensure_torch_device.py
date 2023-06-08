import torch

def ensure_torch_device(device):
    """
    指定されたデバイスが torch.device オブジェクトでなければ、新たに torch.device オブジェクトを作成する。

    :param device: デバイス指定（torch.device オブジェクトまたはその名称を表す文字列）。None も許容。
    :type device: torch.device, str, or None
    :returns: torch.device オブジェクトまたは None（入力が None または不適切な場合）
    :rtype: torch.device or None
    :raises: この関数はエラーメッセージを出力するが、例外は上げない。
    """

    if device is None:
        return None
    if not isinstance(device, torch.device):
        try:
            device = torch.device(device)
        except Exception as e:
            print(f"Error: {e}")
            return None
    return device
