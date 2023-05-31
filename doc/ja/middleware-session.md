# セッションミドルウェア

開いたブラウザでWebチャットをするときにマルチラウンドの会話を成立するためには
ChatPrompt（会話履歴） が複数ターンの会話のなかで更新されていく必要があります。

デフォルトでは、 ChatStream は HTTP セッションを使用してWebアプリケーションをステートフルにし、
ChatPrompt をブラウザが開いている間保持することができます。

HTTP セッションを使用するには、以下のように FastAPI のミドルウェアを登録します。

```python
from fastsession import FastSessionMiddleware, MemoryStore
app.add_middleware(FastSessionMiddleware,
                   secret_key="your-session-secret-key",
                   store=MemoryStore(),
                   http_only=True,
                   secure=True,
                   )
```

|パラメータ名|説明|
|:----|:----|
|secret_key|クッキーの署名用キー。|
|store|セッションの保存用ストア。|
|http_only|クッキーがクライアントサイドのスクリプト（JavaScriptなど）からアクセスできないようにするか。デフォルトはTrue。|
|secure|ローカル開発環境のためにFalse。本番環境ではTrue。Httpsが必要。|

## 内部処理

このデフォルトの実装では、セッションID を生成し署名をほどこしたのち、クッキーに保存します。

クッキーの保存期間はブラウザが開いている間のみで、かつ、フロントエンドのJavaScript からアクセスできない状態となっています

# 会話履歴を永続化するその他の方法

デフォルトの実装では ChatPrompt はセッション上に存在します。 またセッション情報はサーバー側でオンメモリで管理され、セッションの持続期間はブラウザが開いている間でした。

本格的なチャットサーバーを構築する場合は、ユーザーを認証し、ユーザーにひもづいた ChatPrompt をデータベース上に保存（永続化）するのが一般的です。

このような処理を行うためには、[カスタムリクエストハンドラの実装](request-handler-how-to.md)　を行い、リクエストハンドラ上で、 ChatPrompt の管理と、永続化を行うことができます。

## 関連：CORS ミドルウェア

[CORS ミドルウェア](middleware-cors.md)
