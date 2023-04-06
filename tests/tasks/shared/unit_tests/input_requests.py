from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Input requests from Script"


@exec_ui(input_request=("Yes / No [Y/n]",), display_name="Yes or No?")
def yes_or_no_question():

    print("There should be a dialog appearing with a Yes or No question...", flush=True)

    response = input("Yes / No [Y/n]")
    print(f"{response = }", flush=True)


@exec_ui(input_request=("Continue / Abort [Y/n]",), display_name="Continue or Abort?")
def continue_or_abort_question():

    print("There should be a dialog appearing with a Continue or Abort question...", flush=True)

    response = input("Continue / Abort [Y/n]")
    print(f"{response = }", flush=True)


@exec_ui(input_request=("Yes / No [Y/n]",), display_name="Empty Input Prompt")
def no_prompt_question():
    """
    The purpose of this test is to see how the GUI reacts to an input request without a prompt.
    """
    print("There should be a dialog appearing with a Yes or No question...", flush=True)

    response = input()
    print(f"{response = }", flush=True)


@exec_ui(input_request=("no match [x]",), display_name="Non Matching Input Prompt")
def no_match_question():
    """
    The purpose of this test is to see how the GUI reacts to an input request with a prompt that doesn't
    match the input_request argument..
    """
    print("There should be a dialog appearing with a Yes or No question...", flush=True)

    response = input("Yes / No [Y/n]")
    print(f"{response = }", flush=True)


@exec_ui(display_name="No input expected")
def no_input_expected():
    """
    The purpose of this test is to check the behaviour of the GUI when an input statement is used,
    but no `input_request` argument was given to the decorator.

    This will hang the GUI forever when the GUI App or Scripts Runnable is selected. The Jupyter kernel
    can detect this and react properly.
    """

    print("An input request will be the next action ...", flush=True)

    response = input("Yes / No [Y/n]")
    print(f"{response = }", flush=True)
