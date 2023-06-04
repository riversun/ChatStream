# What is ChatPrompt?

ChatPrompt is a class for generating prompts for pre-trained language models (hereafter referred to as models). We call it a prompt class.

For example, in the case of **redpajama-incite**, the following prompt is created and entered into the model.

```text
<human>: Who is Alan Turing
<bot>: Who is Alan Turing
```

The model will then generate the following sentence and output the following.

```text
<human>: Who is Alan Turing
<bot>: He was a very honorable man.
```

In this example, `<human>` and `<bot>` are followed by `:` and separated by `\n`.

These rules and conventions vary slightly from model to model.

The class that generates the prompts and keeps the conversation history is ChatPrompt, which is called the **prompt class**.

As mentioned above, since each model has its own mannerisms, we need a **prompt class** for each model.

### Preset Prompt Classes

ChatStream provides prompt classes = **ChatPrompt classes** for some well-known models.

You can see how to import the prompt class for the model you want to use from the list below.

- [ - Prompt class list](chat-prompt-presets.md)


### Creating your own prompt classes

If there is no prompt class yet, such as in a new model, you can create your own.

- [ - How to implement prompt classes](chat-prompt-how-to-impl.md)