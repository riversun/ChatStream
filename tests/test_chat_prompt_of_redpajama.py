import pytest

from chatstream import AbstractChatPrompt


class ChatPromptRedpajamaInciteForTest(AbstractChatPrompt):

    def __init__(self):
        super().__init__()  # Call the initialization of the base class
        self.set_requester("<human>")
        self.set_responder("<bot>")

    def get_stop_strs(self):
        if not self.chat_mode:
            return None

        return [
            '<|endoftext|>',
            '\n<'
            # Safety stop valve when the model generates not only AI conversations but also human parts of the conversation.
        ]

    def create_prompt(self):
        """
        Build prompts according to the characteristics of each language model
        :return:
        """
        if self.chat_mode == False:
            return self.get_requester_last_msg()

        # Chat Mode == True case
        ret = self.system;
        for chat_content in self.chat_contents:
            chat_content_role = chat_content.get_role()
            chat_content_message = chat_content.get_message()
            if chat_content_role:
                if chat_content_message:
                    merged_message = chat_content_role + ": " + chat_content_message + "\n"
                else:
                    merged_message = chat_content_role + ":"
                ret += merged_message

        return ret


@pytest.fixture
def chat_prompt():
    """
    Pytest fixture that provides a pre-configured instance of the `ChatPromptRedpajamaInciteForTest` class for testing.

    This fixture initializes a `ChatPromptRedpajamaInciteForTest` instance with "<human>" as requester and "<bot>" as responder.
    It then adds a requester message "Who is Alan Turing" and a responder message "He is a nice guy".

    The instance created by this fixture can be used in multiple test functions, which avoids duplicate setup code and makes tests cleaner.

    :return: An instance of `ChatPromptRedpajamaInciteForTest` set up with specified initial conditions.
    """
    chat_prompt = ChatPromptRedpajamaInciteForTest()
    chat_prompt.set_requester("<human>")
    chat_prompt.set_responder("<bot>")
    chat_prompt.add_requester_msg("Who is Alan Turing")
    chat_prompt.add_responder_msg("He is a nice guy")
    return chat_prompt


def test_turn(chat_prompt):
    """
    Test if the 'get_turn' method correctly returns the number of turns taken in the conversation.
    In this test case, we expect it to be 1 as one pair of requester and responder message has been added.
    """
    assert chat_prompt.get_turn() == 1


def test_chat_mode(chat_prompt):
    """
    Test if the chat mode is correctly set to True upon initialization.
    """
    assert chat_prompt.is_chat_mode_enabled() == True


def test_system(chat_prompt):
    """
    Test if the 'system' attribute is correctly set to an empty string upon initialization.
    """
    assert chat_prompt.system == ""


def test_requester(chat_prompt):
    """
    Test if the 'requester' attribute is correctly set to '<human>' upon initialization.
    """
    assert chat_prompt.requester == "<human>"


def test_responder(chat_prompt):
    """
    Test if the 'responder' attribute is correctly set to '<bot>' upon initialization.
    """
    assert chat_prompt.responder == "<bot>"


def test_stop_strs(chat_prompt):
    """
    Test if the 'get_stop_strs' method correctly returns the stop strings for chat mode.
    The expected stop strings are [  '<|endoftext|>',, '\n<'].
    """
    assert chat_prompt.get_stop_strs() == ['<|endoftext|>', '\n<']


def test_create_prompt(chat_prompt):
    """
    Test if the 'create_prompt' method correctly creates and returns the prompt string.
    In this test case, we expect it to be '<human>: Who is Alan Turing\n<bot>: He is a nice guy\n'
    """
    assert chat_prompt.create_prompt() == "<human>: Who is Alan Turing\n<bot>: He is a nice guy\n"


def test_last_requester_message(chat_prompt):
    """
    Test if the 'get_requester_last_msg' method correctly returns the last message added by the requester.
    In this test case, we expect it to be 'Who is Alan Turing'.
    """
    assert chat_prompt.get_requester_last_msg() == "Who is Alan Turing"


def test_last_responder_message(chat_prompt):
    """
    Test if the 'get_responder_last_msg' method correctly returns the last message added by the responder.
    In this test case, we expect it to be 'He is a nice guy'.
    """
    assert chat_prompt.get_responder_last_msg() == "He is a nice guy"
