import logging

from gui_executor.exec import exec_task

_LOGGER = logging.getLogger(__name__)


@exec_task()
def renderable_output(value: float = 42) -> str:
    # This task is to test a problem with rendering a string that containes text between square brackets.
    #
    # If you remove the blank after the opening bracket, the GUI will crash!

    # msg = f"{value = } [no units]"
    msg = (
        "renderable_output "
        "[ /Users/rik/Documents/PyCharmProjects/plato-test-scripts/src/camtest/tasks/mine/output.py:renderable_output:11]: "
        "0.001 seconds"
    )
    # msg = (
    #     "renderable [ /Users/rik/Documents/PyCharmProjects/renderable_output] 0.001 seconds"
    # )
    print(msg)
    _LOGGER.info(msg)
    return msg
