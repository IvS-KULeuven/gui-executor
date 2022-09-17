from __future__ import annotations

import datetime
from pathlib import Path

MAGIC_ID = "# [3405691582]"


# TODO:
#   * write >>> before each line and ... on continuation lines (maybe not such a good idea)
#   * write a timestamp to the file on input and a duration on result

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
    def __init__(self, location: Path | str):
        today = f"{datetime.date.today()}-i"
        filename = Path(location).expanduser() / today

        self.fd = open(filename.with_suffix(".txt"), mode='a')

    def __call__(self, info):
        lines = process_info(info)
        self.fd.writelines(lines)
        self.fd.flush()

    def __del__(self):
        self.fd.close()


class ResultProcessor:
    def __init__(self, location: Path | str):
        today = f"{datetime.date.today()}-r"
        filename = Path(location).expanduser() / today

        self.fd = open(filename.with_suffix(".txt"), mode='a')

    def __call__(self, result):
        self.fd.writelines(process_info(result.info))

        if result.error_before_exec:
            self.fd.write(f"ERROR: {result.error_before_exec}\n")
        if result.error_in_exec:
            self.fd.write(f"ERROR: {result.error_in_exec}\n")

        self.fd.flush()

    def __del__(self):
        self.fd.close()


input_processor = InputProcessor('~')
result_processor = ResultProcessor('~')


def load_ipython_extension(ipython):
    # ipython.input_transformers_post.append(input_processor)
    ipython.events.register('pre_run_cell', input_processor)
    ipython.events.register('post_run_cell', result_processor)


def unload_ipython_extension(ipython):
    ipython.events.unregister('pre_run_cell', input_processor)
    ipython.events.unregister('post_run_cell', result_processor)
