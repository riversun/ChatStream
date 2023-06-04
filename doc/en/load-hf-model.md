# Loading HuggingFace Models

Load the HuggingFace model using the method specified for each model.

```python
model_path = "togethercomputer/RedPajama-INCITE-Chat-3B-v1"
device = "cuda"  # "cuda" / "cpu"

tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)
```

For multi-GPU setups, you can use the method described in [Loading Models Compatible with Multi-GPU](load-hf-model-multi-gpu.md).