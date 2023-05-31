# モックレスポンスの利用（高速起動）

モックレスポンスを使用すると読み込みに時間のかかる事前学習済言語モデルのかわりに、ダミーの文章を生成させることができます

## 使用方法

```python
chat_stream = ChatStream(
    use_mock_response=True,
    mock_params={"type": "echo", "initial_wait_sec": 1, "time_per_token_sec": 1},
    chat_prompt_clazz=ChatPrompt,
)
```

ChatStream クラスのコンストラクタ引数

- **use_mock_response** ... True モックレスポンスを有効にする。  
- **mock_params** ... モックレスポンスの生成ルールを指定する  
- **chat_prompt_clazz** ... プロンプト履歴管理クラス  

**mock_params** パラメータ

|パラメータ名|パラメータ値|説明|
|:----|:----|:----|
|type|round|100ワード程度のダミー文章をラウンドロビン方式で生成する|
| |long|長文のダミー文章を生成する|
| |echo|ユーザーが入力した文字列をそのまま返す|
|initial_wait_sec|数値(秒)|文章生成開始までの待ち時間を 秒 で指定する|
|time_per_token_sec|数値(秒)|１トークンあたりの生成時間。|




