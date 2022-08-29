from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Input requests from Script"


@exec_ui(input_request=("Yes / No [Y/n]",), display_name="YesNoDialog")
def yes_or_no_question():

    print("There should be a dialog appearing with a Yes or No question...", flush=True)

    response = input("Yes / No [Y/n]")
    print(f"{response = }", flush=True)
