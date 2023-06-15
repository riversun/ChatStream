import os
import psutil
import torch


def get_resource_usage(opts={}):
    """
    リソース使用状況を取得する。

    Parameters:
    opts (dict): オプション情報を持つ辞書。"num_gpus"と"device"をキーとして含む。

    Returns:
    dict: CPUとGPUのメモリ使用状況を含む辞書。
    """

    # オプションからGPU数とデバイス情報を取得
    num_gpus = opts.get("num_gpus")
    device = opts.get("device")

    # 返り値となる辞書を初期化
    ret = {
        "num_gpus": None,
        "gpus": [],
        "cpu": {
            "total_memory": 0,
            "used_memory": 0,
        }
    }

    # CPUのメモリ使用状況を取得
    process = psutil.Process(os.getpid())
    cpu_mem_info = process.memory_info().rss
    used_cpu_memory_in_gb = cpu_mem_info / (1024 ** 3)
    total_cpu_memory_in_gb = psutil.virtual_memory().total / (1024 ** 3)

    # 返り値辞書にCPUのメモリ情報を追加
    ret["num_gpus"] = num_gpus
    ret["cpu"]["total_memory"] = round(total_cpu_memory_in_gb, 2)
    ret["cpu"]["used_memory"] = round(used_cpu_memory_in_gb, 2)

    # GPUのメモリ使用状況を取得
    if num_gpus == 0 or str(device) == 'cpu':
        pass
    elif num_gpus == 1:
        index = 0
        if str(device) == 'cuda':
            index = 0
        else:
            index = int(str(device).split(':')[1])

        mem_get_info = torch.cuda.mem_get_info(index)  # returns the total, unused GPU memory
        total = mem_get_info[1] / (1024 ** 3)
        unused = mem_get_info[0] / (1024 ** 3)
        used = total - unused
        ret["gpus"].append({"index": index, "total_memory": round(total, 2), "used_memory": round(used, 2)})

    elif num_gpus > 1:
        num_installed_gpus = torch.cuda.device_count()
        for i in range(num_installed_gpus):
            mem_get_info = torch.cuda.mem_get_info(i)  # returns the total, unused GPU memory
            total = mem_get_info[1] / (1024 ** 3)
            unused = mem_get_info[0] / (1024 ** 3)
            used = total - unused
            ret["gpus"].append({"index": i, "total_memory": round(total, 2), "used_memory": round(used, 2)})


    return ret


if False:
    ret = get_resource_usage({"num_gpus": 1, "device": torch.device("cuda")})
    print(ret)
