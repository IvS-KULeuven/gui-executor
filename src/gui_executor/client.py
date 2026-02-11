import logging
import queue
import time
from typing import List

from jupyter_client import KernelClient

from gui_executor.kernel import MyKernel
from gui_executor.utils import decode_traceback

LOGGER = logging.getLogger("gui-executor.client")
VERBOSE_DEBUG = False


class MyClient:
    def __init__(
        self, kernel: MyKernel, startup_timeout: float = 60.0, timeout: float = 1.0
    ):
        self._timeout = timeout
        """The timeout used when communicating with the kernel."""

        self._startup_timeout = startup_timeout
        """The timeout used when starting up channels to the server."""

        self._error = None

        self._client: KernelClient = kernel._kernel.client()

    def connect(self):
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: Opening channels for client [{self}]...")
        self.start_channels()

    def disconnect(self):
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: Closing channels for client [{self}]...")
        self.stop_channels()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def start_channels(self):
        self._client.start_channels()
        try:
            self.wait_for_ready(timeout=self._startup_timeout)
        except RuntimeError:
            self._client.stop_channels()
            raise
        except AttributeError:
            LOGGER.error(
                f"The client that was created doesn't have the expected method 'wait_for_ready()'. "
                f"The client should be a BlockingKernelClient or an AsyncKernelClient, but it is {type(self._client)}."
            )
            raise

    def wait_for_ready(self, timeout: float = 60.0):
        """Wait for kernel to be ready."""
        self._client.kernel_info()

        start = time.time()
        while True:
            try:
                msg = self._client.get_shell_msg(timeout=1)
                if msg["msg_type"] == "kernel_info_reply":
                    return True
            except Exception:
                pass

            if time.time() - start > timeout:
                raise TimeoutError(
                    "Kernel did not become ready within the specified timeout."
                )
            time.sleep(0.1)

    def stop_channels(self):
        self._client.stop_channels()

    def get_kernel_info(self) -> dict:
        """Returns a dictionary with information about the Jupyter kernel."""
        msg_id = self._client.kernel_info()
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {msg_id = }")

        shell_msg = self._client.get_shell_msg()
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {shell_msg = }")

        return shell_msg["content"]

    # Channel proxy methods ------------------------------

    def get_shell_msg(self, *args, **kwargs):
        """Get a message from the shell channel"""
        return self._client.get_shell_msg(*args, **kwargs)

    def get_iopub_msg(self, *args, **kwargs):
        """Get a message from the iopub channel"""
        return self._client.get_iopub_msg(*args, **kwargs)

    def get_stdin_msg(self, *args, **kwargs):
        """Get a message from the stdin channel"""
        return self._client.get_stdin_msg(*args, **kwargs)

    def get_control_msg(self, *args, **kwargs):
        """Get a message from the control channel"""
        return self._client.get_control_msg(*args, **kwargs)

    def get_error(self):
        return self._error

    def clear_error(self):
        self._error = None

    def input(self, input_string: str):
        """
        Send a string of raw input to the kernel.

        This should only be called in response to the kernel sending an `input_request` message on the stdin channel.
        """

        self._client.input(input_string)

    def execute(self, snippet: str, allow_stdin: bool = True) -> str:
        return self._client.execute(f"{snippet}\n", allow_stdin=allow_stdin)

    def run_snippet(self, snippet: str, allow_stdin: bool = True):
        msg_id = self._client.execute(f"{snippet}\n", allow_stdin=allow_stdin)

        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {msg_id = }")

        # fetch the output

        output: List[str] = []

        while True:
            try:
                io_msg = self._client.get_iopub_msg(timeout=self._timeout)
                io_msg_type = io_msg["msg_type"]
                io_msg_content = io_msg["content"]

                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: io_msg = {io_msg}")
                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: io_msg_type = {io_msg_type}")
                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: io_msg_content = {io_msg_content}")

                if io_msg_type == "status":
                    if io_msg_content["execution_state"] == "idle":
                        # self.signals.data.emit("Execution State is Idle, terminating...")
                        if VERBOSE_DEBUG:
                            LOGGER.debug(
                                f"{id(self)}: Execution State is Idle, terminating..."
                            )
                        break
                elif io_msg_type == "stream":
                    if "text" in io_msg_content:
                        text = io_msg_content["text"].rstrip()
                        output.append(text)
                elif io_msg_type == "display_data":
                    ...  # ignore this message type
                elif io_msg_type == "execute_input":
                    ...  # ignore this message type
                elif io_msg_type == "error":
                    ...  # ignore this message type
                elif io_msg_type == "execute_result":
                    ...  # ignore this message type
                else:
                    raise RuntimeError(f"Unknown io_msg_type: {io_msg_type}")
            except queue.Empty:
                ...

        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {output = }")

        # fetch the reply message

        reply = self._client.get_shell_msg(timeout=1.0)

        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {type(reply) = }")
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {reply = }")
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {reply['content'] = }")

        if reply["content"]["status"] == "error":
            try:
                self._error = decode_traceback(reply["content"]["traceback"])
            except KeyError:
                self._error = "An error occurred, no traceback was provided."
        else:
            self._error = None

        return "\n".join(output)

    def __del__(self):
        if self._client:
            self._client.stop_channels()
