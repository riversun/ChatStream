# Loading Models Compatible with Multi-GPU

In cases where the number of parameters in a model is so large that it doesn't fit on a single GPU, you can load the model across multiple GPUs if your server has them. 

To do this, you can use the `load_hf_model` function below and specify multiple GPUs for use, such as `num_gpus=2`.

In this case, if there are 4 GPUs on the server and `num_gpus=2` is specified, the 2 GPUs with the lowest GPU IDs are used.

Also, if the GPUs have different memory capacities, you can either match the smallest memory size by specifying `max_gpu_memory`, or not specify `max_gpu_memory` and allocate according to the memory size of each GPU. In this case, `"device_map": "sequential"` is specified.

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


def load_hf_model(model_path: str, device: str = "cuda", num_gpus: int = None, max_gpu_memory: str = None,
                  model_opts={}, tokenizer_opts={}):
    if device == "cpu":
        # When using Redpajama-Incite for CPU-based inference,
        # bfloat16 was recommended, but I thought it was faster to specify no bfloat16.
        kwargs = {}  # "torch_dtype": torch.bfloat16}
    elif device == "cuda":
        kwargs = {"torch_dtype": torch.float16}
        if num_gpus is None:
            num_gpus = 1
            kwargs["device_map"] = "auto"
        elif num_gpus == 1:
            pass
        elif num_gpus > 1:

            kwargs["device_map"] = "auto"

            if max_gpu_memory is None:
                kwargs["device_map"] = "sequential"

                available_gpu_memory_list = get_available_gpu_memory_list(num_gpus)

                max_memory_dict = {}
                for i in range(num_gpus):
                    memory = available_gpu_memory_list[i] * 0.85
                    memory_str = str(int(memory)) + "GiB"
                    max_memory_dict[i] = memory_str
                kwargs["max_memory"] = max_memory_dict
                # for example
                # max_memory_dict= { 0: "8GiB", 1: "10GiB", 2: "6GiB", 3: "13GiB" }
            else:
                max_memory_dict = {}
                for i in range(num_gpus):
                    max_memory_dict[i] = max_gpu_memory
                kwargs["max_memory"] = max_memory_dict


    elif device == "mps":
        kwargs = {"torch_dtype": torch.float16}
    else:
        raise ValueError(f"Invalid device: {device}")

    kwargs.update(model_opts)

    tokenizer = AutoTokenizer.from_pretrained(model_path, **tokenizer_opts)
    model = AutoModelForCausalLM.from_pretrained(model_path,
                                                 **kwargs)

    if (device == "cuda" and num_gpus == 1) or device == "mps":
        model.to(device)
    return model, tokenizer, device


def get_available_gpu_memory_list(max_gpus=None):
    available_gpu_count = torch.cuda.device_count()

    if max_gpus is None:
        num_gpus = available_gpu_count
    else:
        num_gpus = min(max_gpus, available_gpu_count)

    gpu_memory_list = []

    for gpu_id in range(num_gpus):
        with torch.cuda.device(gpu_id):
            device = torch.cuda.current_device()
            gpu_properties = torch.cuda.get_device_properties(device)
            total_memory = gpu_properties.total_memory / (1024 **

 3)
            allocated_memory = torch.cuda.memory_allocated() / (1024 ** 3)
            available_memory = total_memory - allocated_memory
            gpu_memory_list.append(available_memory)
    return gpu_memory_list

```
