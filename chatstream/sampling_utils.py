import torch


def sampling(logits, k=None, p=None, temperature=1.0, past_tokens=None, penalty=None, penalty_method="multiplicative"):
    """
    This function generates a token ID from a distribution of logits, possibly applying top-k sampling,
    top-p (nucleus) sampling, and a penalty to previously selected tokens.

    この関数はlogitsの分布からトークンIDを生成し、可能な場合はtop-kサンプリング、top-p（nucleus）サンプリング、
    そして過去に選択されたトークンへのペナルティを適用する。

    Args:
        logits (torch.Tensor): The logits to sample from.
        k (int, optional): The number of highest-probability tokens to keep for top-k sampling.
        p (float, optional): The cumulative probability cutoff for top-p (nucleus) sampling.
        temperature (float, optional): The temperature for scaling the logits. Default is 1.0 (no scaling).
        past_tokens (list, optional): The list of tokens that have been selected in the past.
        penalty (float, optional): The penalty to apply to the logits of past tokens.
        penalty_method (str, optional): The method for applying the penalty ("multiplicative" or "subtractive").

    Returns:
        token_id (int): The sampled token ID.
    """

    # Apply a penalty to the logits of past tokens
    # 過去のトークンのlogitsにペナルティを適用
    if penalty is not None and past_tokens is not None:
        if penalty_method == "multiplicative":
            for token in past_tokens:
                logits[token] *= penalty
        elif penalty_method == "subtractive":
            for token_id in set(past_tokens):
                logits[token_id] -= penalty

    # Apply top-k sampling
    # top-kサンプリングを適用
    if k is not None:
        top_k = torch.topk(logits, k)
        top_k_indices = top_k.indices
        top_k_values = top_k.values
        # Adjust with Softmax with temperature
        # very nice article below
        # https://shivammehta25.github.io/posts/temperature-in-language-models-open-ai-whisper-probabilistic-machine-learning/
        probabilities = torch.softmax(top_k_values / temperature, dim=-1)  # Apply temperature scaling
        choice = torch.multinomial(probabilities, num_samples=1)
        token_id = int(top_k_indices[choice])
        return token_id

    # Apply top-p (nucleus) sampling
    # top-p（nucleus）サンプリングを適用
    if p is not None:
        sorted_logits, sorted_indices = torch.sort(logits, descending=True)
        cumulative_probs = torch.cumsum(torch.softmax(sorted_logits / temperature, dim=-1),
                                        dim=-1)  # Apply temperature scaling

        sorted_indices_to_remove = cumulative_probs > p
        sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
        sorted_indices_to_remove[..., 0] = 0

        logits[sorted_indices] = sorted_indices_to_remove.type(logits.dtype) * -1e10

    # Generate a token ID from the (possibly modified) distribution of logits
    # （可能な場合は修正された）logitsの分布からトークンIDを生成
    probabilities = torch.softmax(logits / temperature, dim=-1)  # Apply temperature scaling
    token_id = int(torch.multinomial(probabilities, num_samples=1))

    return token_id
