# ChatPrompt Prompt Class Implementation

The role of the prompt class is to

- 1. to output prompts for the model based on user input and previous conversation history
- 2. to properly generate sentences,
    - 2-1. have information about special tokens that stop the generation of sentences
    - 2-2. with conversion information for specific tokens

Each model has its own manner of prompting, so we will implement the different manners of prompting

However, it is not difficult to define the basic rules of sentence concatenation

## Import the base class for the prompt class

Import the `AbstractChatPrompt` class, which is the basis of the prompt class.

```python
from chatstream import AbstractChatPrompt
````

## Override the base class

The `AbstractChatPrompt` class is an abstract class, so we will override the necessary methods

The following is an example implementation of the prompt class for rinna/japanese-gpt-neox-3.6b-instruction-sft

The purpose of this model is to output the following prompt format

```text
User: What tourist attractions do you recommend in Japan? <NL>System: Which area would you like to know about? <NL>User: Please tell me the tourist attractions in Shibuya. <NL>System: I would like to know the tourist attractions in Shibuya. 
````

The implementation is as follows

```python
from chatstream import AbstractChatPrompt


class ChatPromptRinnaJapaneseGPTNeoxInst(AbstractChatPrompt):
    def __init__(self):
        super().__init__()
        self.set_requester("User")  # Specify the role name of the requester for the model
        self.set_responder("System")  # Specify the role name of the person = model that responds

    def get_stop_strs(self):
        return []   #If you want to stop sentence generation when a certain keyword comes in, list the keyword here

    def get_replacement_when_input(self):
        return [("\n", "<NL>")]  # Replacement rule for input text when input

    def get_replacement_when_output(self):
        return [("<NL>", "\n")]  # Replacement rule for output text when output

    def create_prompt(self, opts={}):
        # build the prompt
        ret = self.system
        
        # get_contents to get a list of previous conversation history
        for chat_content in self.get_contents(opts):
            # get role name
            chat_content_role = chat_content.get_role()
            # get message
            chat_content_message = chat_content.get_message()

            if chat_content_role:

                if chat_content_message:
                    # if message part exists
                    merged_message = chat_content_role + ": " + chat_content_message + "<NL>"
                else:
                    merged_message = chat_content_role + ": "

                ret += merged_message

        return ret

    def build_initial_prompt(self, chat_prompt):
        # don't implement the initial prompt
        pass

```
## Implementing the prompt class: setting roles

- In the constructor, call `__init__()` in the base class
- For 2-way chat, use `set_requester` and `set_responder` to specify role names.
 
```python
def __init__(self):
    super().__init__()
    self.set_requester("User")  
    self.set_responder("System")  
```

If you need a system-wide initialization message, use the `set_system` method to set the system message.
 
```python
def __init__(self):
    super().__init__()
    self.set_system("The chat system consists of a user and a system. The system tries to answer the user politely and accurately.")
    self.set_requester("User")  # specify the role name of the requester for the model
    self.set_responder("System")  # set the role name of the responder = model
```

## Implementing the prompt class: setting a stop string

- If a stop string is specified, sentence generation can be stopped when a specific keyword or token appears.
- If not specified, use `return []`.
- Stop string and EOS token are different. The stop string is different from the EOS token.
  If you do not specify a stop string here, the EOS token (tokenizer.eos_token_id) preconfigured in the tokenizer will also stop the generation of sentences.

 
```python
def get_stop_strs(self):
    return ['</s>']  ## Stop sentence generation when '</s>' appears.

```

## Implementing the prompt class: setting up replacement rules for input text

Chat implementations basically input the text entered by the user into the model, but there are cases where characters that cannot be entered into the model or need to be converted when entered into the model.

For example, if the user input contains `\n` (line break), but the model cannot accept `\n`, then `\n` must be replaced with the appropriate string.

To replace user input as it is entered into the model, specify the following

```python
def get_replacement_when_input(self):
    return [("\n", "<NL>")]  # Input text replacement rules for input text when entering


```

Here we specify to replace `\n` with `<NL>`. The combination is specified as a tuple like `("\n","<NL>")`.
If you want to register multiple substitution patterns, specify multiple tuples.

## Implementing the prompt class: setting up replacement rules for output text

You can replace keywords that appear in the text output by the model.

For example, if the model output is `Good morning. <NL>What can I do for you?
You can replace the output as follows

```python
def get_replacement_when_output(self):
    return [("<NL>", "\n")]  # Output text replacement rules for output

```

## Implementing the Prompt Class: Generating Prompts

The `create_prompt` method generates an entire prompt including past conversation history.

The past conversation history can be retrieved with `self.get_contents()`.

The return value of `get_contents` is a list whose value contains an instance of the ChatContent class

The ChatContent class stores a single chat content, `chat_content.getRole()` stores the role name, `chat_content.get_message()` stores the message of the role, `chat_content.get_text()` stores the text of the message, `chat_content.get_text()` stores the message of the role.
to get the role name, and `chat_content.get_message()` to get the text of the role's message.

By writing the logic to link them together, you can generate prompts in the format expected by the model.

```python
def create_prompt(self, opts={}):
  
  # We start building the prompt
  ret = self.system;
  # We obtain the history of the conversation list using get_contents
  for chat_content in self.get_contents(opts):
      # We get the role name
      chat_content_role = chat_content.get_role()
      # We get the message
      chat_content_message = chat_content.get_message()
  
      if chat_content_role:
  
          if chat_content_message:
              # If there is a message part
              merged_message = chat_content_role + ": " + chat_content_message + "<NL>"
          else:
              merged_message = chat_content_role + ": "
  
          ret += merged_message
  
  return ret
```
## Implementing a prompt class: generating initial prompt and initial context

Depending on the model, you may want to set up some conversational context in advance.

To have the model suddenly input a sentence is called a "zero shot",
However, if some input is provided in advance, such as prerequisite knowledge or examples, the output may be more stable afterwards.

This is called a one-shot or a fourshot.

(In the case of chat, it is also used to start a conversation from a specific topic, etc.)

The following is an example of starting a chat with the movie "Titanic" as the initial context

Override the `build_initial_prompt` method

```python
def build_initial_prompt(self, chat_prompt):
    chat_prompt.add_requester_msg("Do you know about the Titanic movie?")
    chat_prompt.add_responder_msg("Yes, I am familiar with it.")
    chat_prompt.add_requester_msg("Who starred in the movie?")
    chat_prompt.add_responder_msg("Leonardo DiCaprio and Kate Winslet.")
```