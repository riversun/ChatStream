# プロンプトクラス一覧

以下にあるHuggingFace 事前学習済言語モデル一覧から使いたいモデルを開くと、対応するプロンプトクラスのインポート方法が確認できます

<details>
<summary>rinna/japanese-gpt-neox-3.6b-instruction-sft</summary>

**プロンプトクラス**

- ChatPromptRinnaJapaneseGPTNeoxInst

**対象モデル**

[rinna/japanese-gpt-neox-3.6b-instruction-sft](https://huggingface.co/rinna/japanese-gpt-neox-3.6b-instruction-sft)


**主要対応言語**

- 日本語

**インポート方法**

```python
from chatstream import ChatPromptRinnaJapaneseGPTNeoxInst as ChatPrompt
```
</details>



<details>
<summary>together/RedPajama-INCITE-Chat-3B-v1</summary>

**プロンプトクラス**

- ChatPromptTogetherRedPajamaINCITEChat

**対象モデル**

[together/RedPajama-INCITE-Chat-3B-v1](https://huggingface.co/togethercomputer/RedPajama-INCITE-Chat-3B-v1)


**主要対応言語**

- 英語

**インポート方法**

```python
from chatstream import ChatPromptTogetherRedPajamaINCITEChat as ChatPrompt
```
</details>
