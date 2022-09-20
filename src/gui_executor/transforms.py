from __future__ import annotations

import atexit
import datetime
import os
import sys
from pathlib import Path
from typing import IO
from typing import Optional

MAGIC_ID = "# [3405691582]"

last_input_ts = datetime.datetime.now(tz=datetime.timezone.utc)

# TODO:
#   * NOT DONE - write >>> before each line and ... on continuation lines (maybe not such a good idea)
#   * DONE - write a timestamp to the file on input and a duration on result
#   * DONE - Allow the user to set the command log file location -> --cmd-log

def process_info(info):
    lines = info.raw_cell.splitlines(keepends=True)
    if not lines:
        return []
    if MAGIC_ID in lines[0]:
        lines = [line.replace(MAGIC_ID, "", 1).lstrip() for line in lines if MAGIC_ID in line]
    if not lines[-1].endswith('\n'):
        lines.append('\n')
    return lines


class InputProcessor:
    def __init__(self, fd):
        global last_input_ts
        self.fd = fd
        last_input_ts = datetime.datetime.now(tz=datetime.timezone.utc)

    def __call__(self, info):
        global last_input_ts
        last_input_ts = datetime.datetime.now(tz=datetime.timezone.utc)
        # lines = process_info(info)
        # self.fd.writelines(lines)
        self.fd.write(f"# <-- {last_input_ts}\n")
        self.fd.flush()

    def __del__(self):
        self.fd.close()


class ResultProcessor:
    def __init__(self, fd):
        self.fd = fd

    def __call__(self, result):
        global last_input_ts
        now = datetime.datetime.now(tz=datetime.timezone.utc)

        self.fd.writelines(process_info(result.info))

        if result.error_before_exec:
            self.fd.write(f"# ERROR: {result.error_before_exec}\n")
        if result.error_in_exec:
            self.fd.write(f"# ERROR: {result.error_in_exec}\n")

        self.fd.write(f"# --> duration: {(now - last_input_ts).total_seconds()}s\n")
        self.fd.flush()

    def __del__(self):
        self.fd.close()


command_log_file_location = os.environ.get("GUI_EXECUTOR_CMD_LOG_FILE_LOCATION", None)
command_log_file_fd: Optional[IO] = None
input_processor = None
result_processor = None


def open_command_log_file() -> IO | None:
    global command_log_file_location
    global command_log_file_fd

    if command_log_file_location is None:
        print("You need to provide the command_log_file_location")
        return None

    filename = Path(command_log_file_location).expanduser() / f"{datetime.date.today()}-cmd-log.txt"
    command_log_file_fd = open(filename, mode='a')

    return command_log_file_fd


def close_command_log_file():
    global command_log_file_fd

    if command_log_file_fd is not None:
        command_log_file_fd.close()


atexit.register(close_command_log_file)


def set_log_file_location(path: str):
    global command_log_file_location

    if not Path(path).expanduser().exists():
        print(f"The path that you provided doesn't exist: {path}")
        return

    command_log_file_location = str(Path(path).expanduser().resolve())


def load_ipython_extension(ipython):
    global input_processor, result_processor
    global command_log_file_fd, command_log_file_location

    if open_command_log_file() is None:
        return

    input_processor = InputProcessor(command_log_file_fd)
    result_processor = ResultProcessor(command_log_file_fd)
    # ipython.input_transformers_post.append(input_processor)
    print(f"Loading IPython extension 'gui_executor.transforms'... command log file={command_log_file_fd.name}")
    ipython.events.register('pre_run_cell', input_processor)
    ipython.events.register('post_run_cell', result_processor)


def unload_ipython_extension(ipython):
    print("Unloading IPython extension 'gui_executor.transforms'...")

    if input_processor is not None:
        ipython.events.unregister('pre_run_cell', input_processor)
    if result_processor is not None:
        ipython.events.unregister('post_run_cell', result_processor)

    close_command_log_file()
