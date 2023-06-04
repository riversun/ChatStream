# Adding a Progress Bar to Model Loading Time

The model loading time is uncertain, but a progress bar can be displayed during loading.

The first time the process is run, the processing time is measured. The second time, or when the same process is called again, a progress bar is displayed.

<img src="https://riversun.github.io/loadtime/loadtime_std.gif">

Just by wrapping the model loading with `LoadTime`, you can load with a progress bar.

**Before** 

```python
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
```

↓
↓


**After**

```python
from chatstream import LoadTime
model = LoadTime(name=model_path,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()
```

**Complete Model Loading Source Code**

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from loadtime import LoadTime

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"

model = LoadTime(name=model_path,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()

tokenizer = AutoTokenizer.from_pretrained(model_path) # The tokenizer is obtained after model loading
```