import sys
import time

from gui_executor.exec import exec_ui


@exec_ui()
def raise_a_value_error():
    """This function just raises a ValueError after it first sleeps for 1s."""
    print("This function will raise a ValueError after 1s...", flush=True)
    print("This message is sent to stderr.", file=sys.stderr)
    # time.sleep(1.0)
    raise ValueError("Exception raised as an example..")


@exec_ui()
def return_a_value_error() -> Exception:
    try:
        raise ValueError("Value Error not raised, but returned.")
    except Exception as exc:
        return exc
