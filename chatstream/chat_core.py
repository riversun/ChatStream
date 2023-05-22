import asyncio

import torch

from .sampling_utils import sampling


async def process_chat(model, tokenizer, device, params, prompt):
    """
    指定された生成条件によって、文章生成を行う。
    
    事前学習済言語モデルによる並行トークン生成（非同期タスク）に対応。

    【文章生成について】
    文章生成は条件(params)によってモデルによる逐次文章生成をコントロールする
    また、停止ワードや停止トークンを監視し、必要なタイミングで文章生成を停止させる

    【複数のリクエストの並行処理について】
    FastAPIは非同期I/Oをサポートしており、これは複数のリクエストを並行に処理する能力がある。
    FastAPI（というかPythonの）非同期I/Oは、コルーチンと呼ばれる特殊な関数を使用して並行性を実現している。
    この場合の並行性とは、一度に一つのタスクだけが進行するが、I/O操作（HTTPリクエスト、モデルからのトークンの生成など）を待つ間に他のタスクを進行させることができる
    ということ。この形式を"協調的マルチタスク"を呼ぶ。
    それぞれのリクエストは別の「非同期タスク」として処理され、これらのタスクは同じスレッド上で切り替えられる。
    「非同期タスク」においては複数のリクエストに対するモデルへのアクセスが並行しているように見えるが
    実際にはある瞬間に一つのリクエストだけがモデルを利用している。
    そのため、それぞれのリクエストが　モデルによるトークン生成のためにブロックする期間は限られており、
    逐次出力トークンの生成について言えば、１つ新トークンを生成した後で他のリクエストに制御を戻すことができる。
    そのために、本メソッド内のforループ内で１つトークンを生成する毎に await asyncio.sleep(0) を呼び出し、
    他のタスクが進行できる（制御を移す）チャンスを与えるようにしている。
    そのため、一つのリクエストによる文章生成の際、停止トークン、停止文字列が現れるまでの間、
    他の全てのリクエストがブロックされることはなく、各リクエストはモデルからのトークンを逐次生成しながら、
    他のリクエストも進行させることができる。


     :param model: 
     :param tokenizer: 
     :param device: 
     :param params: 
        paramsの例
             {
    "temperature": 0.7,  # Temperatureの値
                             "max_new_tokens": 256,  # 新たに生成する最大トークンサイズ（何トークン分か。)
                             "context_len": 1024,  # コンテクストのサイズ（何トークン分か。)
                             "use_top_k_sampling": True,  # True: top K サンプリングを有効にする
                             "top_k_value": 50,  # top K サンプリングの値。
                             "use_top_p_sampling": True,  # True: top P サンプリングを有効にする
                             "top_p_value": 0.7,  # top P サンプリングの値
                             "use_repetition_penalty": False,  # True:繰り返し同じトークンを生成したときのペナルティを有効する
                             "repetition_penalty": 1,  # ペナルティの値
                             "repetition_penalty_method": "multiplicative"  # ペナルティの計算方法
             },     
     :param prompt: 

    """
    stream_interval = 1

    temperature = float(params.get("temperature", 1.0))
    max_new_tokens = int(params.get("max_new_tokens", 256))
    context_len = int(params.get("context_len", 1024))
    stop_strs = params.get("stop_strs", None)
    force_set_bos_token_id = params.get("force_set_bos_token_id", None)
    force_set_eos_token_id = params.get("force_set_eos_token_id", None)

    add_special_tokens = params.get("add_special_tokens", None)

    use_top_k_sampling = params.get("use_top_k_sampling", True)
    top_k_value = params.get("top_k_value", 50)

    use_top_p_sampling = params.get("use_top_p_sampling", True)
    top_p_value = params.get("top_p_value", 1.0)

    use_repetition_penalty = params.get("use_repetition_penalty", False)

    repetition_penalty = params.get("repetition_penalty", 1),
    repetition_penalty_method = params.get("repetition_penalty_method", "multiplicative")
    use_bos_for_input = params.get("use_bos_for_input", False)

    if force_set_bos_token_id:
        # patch for open_llama_7b_preview_300bt
        tokenizer.bos_token_id = force_set_bos_token_id

    if force_set_eos_token_id:
        # patch for open_llama_7b_preview_300bt
        stop_token_ids = params.get("stop_ids", [force_set_eos_token_id])
    else:
        stop_token_ids = params.get("stop_ids", [tokenizer.eos_token_id])

    len_prompt = len(prompt)

    if use_bos_for_input:
        # force add bos
        input_ids = [tokenizer.bos_token_id] + tokenizer(prompt).input_ids
        len_prompt -= len(tokenizer.decode([tokenizer.bos_token_id]))
    else:
        if add_special_tokens is None:
            # tokenizer __call__ だと自動的に特殊トークンを入れてしまう模様.
            input_ids = tokenizer(prompt).input_ids
        else:
            # 特殊トークンを自動でいれさせないために add_special_token を明示的にマネージする
            input_ids = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)

    output_token_ids = list(input_ids)

    max_src_len = context_len - max_new_tokens - 8
    input_ids = input_ids[-max_src_len:]

    with torch.no_grad():
        for idx in range(max_new_tokens):

            # Insert asyncio.sleep(0) here to yield control after each token is generated
            await asyncio.sleep(0)

            if idx == 0:
                # モデルにテンソルを入力して出力を得る

                out = model(input_ids=torch.as_tensor([input_ids], device=device), use_cache=True)
                logits = out.logits
                past_key_values = out.past_key_values
            else:
                # モデルにテンソルを入力して出力を得る
                out = model(
                    input_ids=torch.as_tensor([[token_id]], device=device),
                    use_cache=True,
                    past_key_values=past_key_values,
                )
                logits = out.logits
                past_key_values = out.past_key_values

            last_token_logits = logits[0][-1]

            if device == "mps":
                last_token_logits = last_token_logits.float().to("cpu")

            if temperature < 1e-4:
                token_id = int(torch.argmax(last_token_logits))
            else:
                token_id = sampling(logits=last_token_logits,
                                    k=top_k_value if use_top_k_sampling else None,
                                    p=top_p_value if use_top_p_sampling else None,
                                    temperature=temperature,
                                    past_tokens=output_token_ids,
                                    penalty=repetition_penalty if use_repetition_penalty else None,
                                    penalty_method=repetition_penalty_method)

            output_token_ids.append(token_id)

            if token_id in stop_token_ids:
                stopped = True
            else:
                stopped = False

            if idx % stream_interval == 0 or idx == max_new_tokens - 1 or stopped:
                output = tokenizer.decode(output_token_ids, skip_special_tokens=True)

                if stop_strs:
                    for stop_str in stop_strs:
                        if stop_str:

                            pos = output.rfind(stop_str, len_prompt)
                            is_stop_str_found = (pos != -1)
                            if is_stop_str_found:
                                output = output[:pos]
                                stopped = True

                yield output

            if stopped:
                break

    del past_key_values
