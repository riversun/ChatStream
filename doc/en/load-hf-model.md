# HuggingFace モデルのロード

モデルごとに指定された方法で HuggingFace モデルを読み込みます

```python
model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"
device = "cuda"  # "cuda" / "cpu"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)
```

マルチGPUの場合は [マルチGPUに対応したモデルの読み込み](load-hf-model-multi-gpu.md) に示す方法をつかうことができます
