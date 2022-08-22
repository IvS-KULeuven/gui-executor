import logging
import queue
import textwrap

import jupyter_client.kernelspec
import rich
from executor import ExternalCommand
from executor import ExternalCommandFailed
from jupyter_client.manager import KernelManager
from rich import print

from gui_executor.utils import remove_ansi_escape

LOGGER = logging.getLogger("gui-executor.kernel")


class KernelError(Exception):
    pass


def decode_traceback(traceback: str) -> str:
    return remove_ansi_escape('\n'.join(traceback))


class MyKernel:

    def __init__(self, name: str = "python3", startup_timeout: int = 60):
        self._kernel = KernelManager(kernel_name=name)
        self._kernel.start_kernel()
        self._client = self._kernel.client()
        self._client.start_channels()
        try:
            self._client.wait_for_ready(timeout=startup_timeout)
        except RuntimeError:
            self._client.stop_channels()
            self._kernel.shutdown_kernel()
            raise
        self._error = None

    def is_alive(self) -> bool:
        return self._kernel.is_alive()

    def shutdown(self):
        self._kernel.shutdown_kernel(now=True)

    @staticmethod
    def get_kernel_specs():
        return jupyter_client.kernelspec.find_kernel_specs()

    def get_kernel_info(self):
        msg_id = self._client.kernel_info()
        # rich.print(f"get_info() -> {msg_id = }")
        reply = self._client.get_shell_msg()
        # rich.print("get_info() -> reply = ", reply)
        return reply

    def get_connection_file(self):
        return self._kernel.connection_file

    def run_snippet(self, snippet: str) -> str:

        # Flush the IOPub channel before executing the command. This is needed because another
        # client might be connected that has sent out messages on the pub channel. We want to
        # catch the output of the given command of course.

        self.flush()

        msg_id = self._client.execute(snippet)
        LOGGER.debug(f"{msg_id = }")

        reply = self._get_response(msg_id)
        LOGGER.debug(f"{type(reply) = }")
        LOGGER.debug(f"{reply = }")
        LOGGER.debug(f"{reply['content'] = }")

        if reply["content"]["status"] == "error":
            try:
                self._error = decode_traceback(reply["content"]["traceback"])
            except KeyError:
                self._error = "An error occurred, no traceback was provided."
        else:
            self._error = None

        output = self._get_output()
        # LOGGER.debug(f"{output = }")

        return output.strip()

    def flush(self):
        while True:
            try:
                _ = self._client.get_iopub_msg(timeout=0.2)
            except queue.Empty:
                break

    def get_error(self) -> str:
        return self._error

    def _get_response(self, msg_id: str = None) -> dict:
        return self._client.get_shell_msg(msg_id)

    def _get_output(self, timeout: float = 1.0) -> str:

        # When the execution state is "idle" it is complete

        io_msg_content = self._client.get_iopub_msg(timeout=timeout)['content']

        if 'execution_state' in io_msg_content and io_msg_content['execution_state'] == 'idle':
            return ""

        while True:
            last_io_msg_content = io_msg_content

            try:
                io_msg_content = self._client.get_iopub_msg(timeout=timeout)['content']
                if 'execution_state' in io_msg_content and io_msg_content['execution_state'] == 'idle':
                    break
            except queue.Empty:
                break

        return self._decode_io_msg_content(last_io_msg_content)

    @staticmethod
    def _decode_io_msg_content(content: dict) -> str:

        if 'data' in content:  # Indicates completed operation
            return content['data']['text/plain']
        elif 'name' in content and content['name'] == "stdout":  # indicates output
            return content['text']
        elif 'traceback' in content:  # Indicates an error
            return decode_traceback(content['traceback'])
        else:
            return ''

    def __del__(self):
        self._client.stop_channels()
        self._kernel.shutdown_kernel()


def do_test_my_kernel(name: str = "python3"):

    kernel = MyKernel(name=name)

    snippets = [
        "a=2",
        textwrap.dedent("""\
            a = 42
            b = 73
            c = a + b
            print(c)        
            """),
        'print(f"{a=}, {b=}, {c=}")',
        '1/0',  # should return a ZeroDivisionError
        'import sys; print(f"{sys.path = }")',
        'import pandas as pd',
        'df = pd.DataFrame(dict(A=[1,2,3], B=["one", "two", "three"]))',
        'df',
        'df.describe()',
        '!pip list -v'
    ]

    for snippet in snippets:
        if out := kernel.run_snippet(snippet):
            print(out)


def start_qtconsole(kernel: MyKernel, buffer_size: int = 5000, console_height: int = 42, console_width: int = 128):
    connection_file = kernel.get_connection_file()
    cmd_line = (f"jupyter qtconsole --ConsoleWidget.buffer_size={buffer_size} "
                f"--ConsoleWidget.console_height={console_height} "
                f"--ConsoleWidget.console_width={console_width} "
                f"--existing {connection_file}")

    cmd = ExternalCommand(
        f"{cmd_line}", capture=True, capture_stderr=True, asynchronous=True)
    try:
        cmd.start()
    except ExternalCommandFailed as exc:
        raise KernelError(cmd.error_message) from exc

    return cmd


if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    # kernel_name = "python3"
    kernel_name = "plato-common-egse"

    do_test_my_kernel(name=kernel_name)
