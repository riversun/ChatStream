# ChatStream の生成と初期化

ChatStream クラスは ChatStream パッケージのコアとなるクラスで、FastAPI/Starlette の Request を受け取り、
負荷制御をしながらストリーミングレスポンスをクライアントに送出する役割をもっています。

以下のように model,tokenizer,device, 最大同時処理数 `num_of_concurrent_executions` 、待ち行列の最大数 `max_queue_size` ,プロンプトクラス ChatPrompt を指定して初期化します

```python
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path, torch_dtype=torch.float16)
model.to(device)

chat_stream = ChatStream(
    num_of_concurrent_executions=2,
    max_queue_size=5,
    model=model,
    tokenizer=tokenizer,
    device=device,
    chat_prompt_clazz=ChatPrompt,
)

```

## オプション一覧

ChatStream の初期化オプション（コンストラクタ引数）一覧

|パラメータ名|説明|
|:----|:----|
|model|HuggingFace形式の事前学習済み言語モデル。|
|tokenizer|HuggingFace形式のトークナイザ。|
|device|実行デバイス。"cpu" / "cuda" / "mps"から選択。|
|num_of_concurrent_executions|事前学習済み言語モデルにおける文章生成タスクの同時実行数。デフォルトは2。|
|max_queue_size|事前学習済み言語モデルにおける文章生成タスクの最大キューサイズ。デフォルトは5。|
|too_many_request_as_http_error|'Too many requests'の状況が発生した場合、ステータスを429として返すかどうか。デフォルトはFalse。|
|use_mock_response|テストのための固定フレーズを返すかどうか。モデルを読み込む必要がないため、すぐに起動する。デフォルトはFalse。|
|mock_params|use_mock_response=Trueの時に返すフレーズのタイプ "round" / "long"。デフォルトは{"type": "round"}。|
|chat_prompt_clazz|言語モデルに送られるプロンプトを管理するクラス。AbstractChatPromptから継承し、各モデルのエチケットに従ったチャットプロンプトを生成するクラスを実装する。|
|max_new_tokens|新たに生成されるトークンの最大サイズ。デフォルトは256。|
|context_len|コンテキストのサイズ（トークン数）。デフォルトは1024。|
|temperature|予測におけるランダム性の温度値。デフォルトは1.0。|
|top_k|サンプリングのためのtop Kの値。デフォルトは50。|
|top_p|サンプリングのためのtop Pの値。デフォルトは1.0。|
|repetition_penalty|繰り返しのペナルティ。デフォルトはNone。|
|repetition_penalty_method|繰り返しのペナルティの計算方法。デフォルトは"multiplicative"。|
|add_special_tokens|トークナイザのオプション。デフォルトはNone。|
|request_handler|リクエストハンドラ。デフォルトでは、セッションを簡単に保持するハンドラがデフォルト。|
|logger|ロギングオブジェクト。デフォルトはNone。|


例）

```python
chat_stream = ChatStream(
     model=None,  # HuggingFace形式の事前学習済み言語モデル
     tokenizer=None,  # HuggingFace形式のトークナイザ
     device=None,  # 実行デバイス "cpu" / "cuda" / "mps"
     num_of_concurrent_executions: int = 2,     # 事前学習済み言語モデルにおける文章生成タスクの同時実行数
     max_queue_size: int = 5,     # 事前学習済み言語モデルにおける文章生成タスクの最大キューサイズ
     too_many_request_as_http_error=False,     # 'Too many requests'の状況が発生した場合、ステータスを429として返す
     use_mock_response=False,     # テストのための固定フレーズを返す。モデルを読み込む必要がないため、すぐに起動する
     mock_params={type: "round"},     # use_mock_response=Trueの時に返すフレーズのタイプ "round" / "long"
     chat_prompt_clazz=None,     # 言語モデルに送られるプロンプトを管理するクラスを指定。AbstractChatPromptから継承し、各モデルのエチケットに従ったチャットプロンプトを生成するクラスを実装する
     max_new_tokens=256,  # 新たに生成されるトークンの最大サイズ
     context_len=1024,  # コンテキストのサイズ（トークン数）
     temperature=1.0,  # 予測におけるランダム性の温度値
     top_k=50,  # サンプリングのためのtop Kの値
     top_p=1.0,  # サンプリングのためのtop Pの値
     repetition_penalty=None,  # 繰り返しのペナルティ
     repetition_penalty_method="multiplicative",  # 繰り返しのペナルティの計算方法
     # トークン関連の処理
     add_special_tokens=None,  # トークナイザのオプション
     request_handler=SimpleSessionRequestHandler(),
     # リクエストハンドラ。デフォルトでは、セッションを簡単に保持するハンドラがデフォルト
     logger=None,  # ロギングオブジェクト
)
```
