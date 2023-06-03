# 時間のかかるモデル読み込みにプログレスバーをつける

モデルの読み込みは処理時間が不明ですが、読み込み時にプログレスバーを表示することができます。

1回目の実行時は処理時間を計測しておき、2回目、また同じ処理が呼ばれたときはプログレスバーを表示します。

<img src="https://riversun.github.io/loadtime/loadtime_std.gif">

モデルの読み込みを `LoadTime` でラップするだけで、プログレスバーつきで読み込むことができます


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

**モデル読み込みソースコード全体**

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from loadtime import LoadTime

model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"

model = LoadTime(name=model_path,
                 fn=lambda: AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16))()

tokenizer = AutoTokenizer.from_pretrained(model_path) # tokenizerはモデル読み込みの後で取得します

```

