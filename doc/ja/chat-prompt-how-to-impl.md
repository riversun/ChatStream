# ChatPrompt プロンプトクラスの実装

プロンプトクラスの役割は以下のとおりです

- １. ユーザーの入力や、これまでの会話履歴をもとにモデル用のプロンプトを出力する
- ２. 文章を適切に生成するため、
    - ２-１. 文章生成を停止する特殊トークンを情報を持つ
    - ２-２. 特定のトークンの変換情報を持つ

プロンプトはモデルごとにお作法が異なるので、そのお作法の違いを実装します

といっても、基本は文章の連結ルールを定義するだけなので難しくありません

## プロンプトクラスの基底クラスのインポート

プロンプトクラスのもととなる、 `AbstractChatPrompt` クラスをインポートします

```python
from chatstream import AbstractChatPrompt
```

## 基底クラスのオーバーライド

`AbstractChatPrompt` クラスは抽象クラスなので、必要なメソッドをオーバーライドしていきます

以下は rinna/japanese-gpt-neox-3.6b-instruction-sft 用のプロンプトクラスの実装例です

このモデルでは、以下のようなプロンプトのフォーマットを出力することが目的です

```text
ユーザー: 日本のおすすめの観光地を教えてください。<NL>システム: どの地域の観光地が知りたいですか？<NL>ユーザー: 渋谷の観光地を教えてください。<NL>システム: 
```

実装は以下のようになります

```python
from chatstream import AbstractChatPrompt


class ChatPromptRinnaJapaneseGPTNeoxInst(AbstractChatPrompt):
    def __init__(self):
        super().__init__()
        self.set_requester("ユーザー")  # モデルに対して要求する側のロール名　を指定します
        self.set_responder("システム")  # 返信する側＝モデル　のロール名　を指定します

    def get_stop_strs(self):
        return []  # あるキーワードが来たら文章生成を停止したい場合はここにキーワードを列挙します

    def get_replacement_when_input(self):
        return [("\n", "<NL>")]  # 入力時の入力テキストの置換ルール

    def get_replacement_when_output(self):
        return [("<NL>", "\n")]  # 出力時の出力テキストの置換ルール

    def create_prompt(self, opts={}):
        # プロンプトを構築していきます
        ret = self.system;
        # get_contents でこれまでの会話履歴リストを取得
        for chat_content in self.get_contents(opts):
            # ロール名を取得
            chat_content_role = chat_content.get_role()
            # メッセージを取得
            chat_content_message = chat_content.get_message()

            if chat_content_role:

                if chat_content_message:
                    # メッセージパートが存在する場合
                    merged_message = chat_content_role + ": " + chat_content_message + "<NL>"
                else:
                    merged_message = chat_content_role + ": "

                ret += merged_message

        return ret

    def build_initial_prompt(self, chat_prompt):
        # 初期プロンプトは実装しない
        pass

```

## プロンプトクラスの実装：ロールの設定

- コンストラクタで、基底クラスの `__init__()` を呼び出します
- ２者間チャットの場合は、 `set_requester` と `set_responder` でロール名を指定します。

```python
def __init__(self):
    super().__init__()
    self.set_requester("ユーザー")  # モデルに対して要求する側のロール名　を指定します
    self.set_responder("システム")  # 返信する側＝モデル　のロール名　を指定します
```

もしシステム全体の初期化メッセージが必要な場合は `set_system` メソッドでシステムメッセージをセットします

```python
def __init__(self):
    super().__init__()
    self.set_system("ユーザーとシステムからなるチャットシステムです。システムはユーザーに対して丁寧かつ正確な回答をするよう心がけます")
    self.set_requester("ユーザー")  # モデルに対して要求する側のロール名　を指定します
    self.set_responder("システム")  # 返信する側＝モデル　のロール名　を指定します
```

## プロンプトクラスの実装：停止文字列の設定

- 停止文字列を指定すると、特定のキーワード、トークンが出現した場合に文章生成を停止させることができます。
- 無指定の場合は `return []` とします
- 停止文字列 と EOSトークン は異なります。ここで停止文字列を無指定にしても
  tokenizer にあらかじめ設定されている EOSトークン （tokenizer.eos_token_id）でも文章生成は停止します。

```python
    def get_stop_strs(self):


    return ['</s>']  # '</s>' が出現したら、そこで文章生成を停止する
```

## プロンプトクラスの実装：入力テキストの置換ルールの設定

チャットの実装では基本的にユーザーが入力した文章をモデルに入力しますが、モデルに入力できない文字やモデルに入力する際に変換が必要になる場合があります。

たとえば、ユーザーが入力した文章に `\n` (改行) が含まれているが、モデルが `\n` を受け付けられない場合は `\n` を適切な文字列に置換する必要があります。

ユーザーの入力をモデルに入力するときに置換するには以下のように指定します

```python
    def get_replacement_when_input(self):


    return [("\n", "<NL>")]  # 入力時の入力テキストの置換ルール
```

ここでは `\n` を `<NL>` に置換するように指定しています。`("\n", "<NL>")` のように組み合わせをタプルで指定します。
複数の置換パターンを登録したいときはこのタプルを複数指定します。

## プロンプトクラスの実装：出力テキストの置換ルールの設定

モデルが出力した文章内に登場するキーワードを置換することができます。

例えば、モデルの出力が `おはようございます。<NL>何か御用でしょうか` だった場合に `<NL>` を 改行を示す `\n` に置換したいときに以下のように設定することで
出力を置換することができます

 ```python
    def get_replacement_when_output(self):


    return [("<NL>", "\n")]  # 出力時の出力テキストの置換ルール
```

## プロンプトクラスの実装：プロンプトの生成

過去の会話履歴を含めたプロンプト全体を生成するのが `create_prompt` メソッドです。

過去の会話履歴は `self.get_contents()` で取得することができます。

`get_contents` の戻り値は リストで、値には ChatContent クラスのインスタンスが格納されます

ChatContent クラスは１件分のチャット内容が格納されており`chat_content.getRole()` でロール名、 `chat_content.get_message()`
でそのロールの発話内容（テキスト）が取得できます。

これらをつなぎあわせるロジックを記述することで、モデルが期待するフォーマットのプロンプトを生成することができます

```python
    def create_prompt(self, opts={}):


# プロンプトを構築していきます
ret = self.system;
# get_contents でこれまでの会話履歴リストを取得
for chat_content in self.get_contents(opts):
    # ロール名を取得
    chat_content_role = chat_content.get_role()
    # メッセージを取得
    chat_content_message = chat_content.get_message()

    if chat_content_role:

        if chat_content_message:
            # メッセージパートが存在する場合
            merged_message = chat_content_role + ": " + chat_content_message + "<NL>"
        else:
            merged_message = chat_content_role + ": "

        ret += merged_message

return ret

```

## プロンプトクラスの実装：初期プロンプト、初期コンテクストの生成

モデルによっては、事前に、ある程度会話のコンテクストを設定しておきたい場合があります。

いきなりモデルに入力して文章させることを ゼロショット と呼びますが、
事前にいくらか入力しておいて、前提知識や、例示などをあたえると、その後の出力が安定する場合があります。

これを ワンショットやフューショット などと呼びます。

チャットの場合はある特定の話題から会話を開始する、などの用途でも用います

以下は初期コンテクストとして、映画「タイタニック」と会話している状態からチャットを開始するための例です

`build_initial_prompt`メソッドをオーバーライドします

```python
def build_initial_prompt(self, chat_prompt):
    chat_prompt.add_requester_msg("Do you know about the Titanic movie?")
    chat_prompt.add_responder_msg("Yes, I am familiar with it.")
    chat_prompt.add_requester_msg("Who starred in the movie?")
    chat_prompt.add_responder_msg("Leonardo DiCaprio and Kate Winslet.")
```