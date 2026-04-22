import logging

from gui_executor.exec import exec_task


@exec_task()
def convert_to_float(value: str = "42") -> float:
    try:
        return float(value)
    except ValueError as e:
        logging.error(f"Could not convert '{value}' to float: {e}")
        raise
