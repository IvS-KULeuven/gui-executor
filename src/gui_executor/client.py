import logging
import queue
import time
from typing import List

from jupyter_client.client import KernelClient

from gui_executor.kernel import MyKernel
from gui_executor.utils import bool_env, decode_traceback

LOGGER = logging.getLogger("gui-executor.client")

VERBOSE_DEBUG = bool_env("VERBOSE_DEBUG")


class MyClient:
    def __init__(self, kernel: MyKernel, startup_timeout: float = 60.0, timeout: float = 1.0):
        self._timeout = timeout
        """The timeout used when communicating with the kernel."""

        self._startup_timeout = startup_timeout
        """The timeout used when starting up channels to the server."""

        self._error = None

        self._client: KernelClient = kernel._kernel.client()

        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: Created client [{type(self._client)}] for kernel [{type(kernel)}].")

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
            if VERBOSE_DEBUG:
                LOGGER.debug("Client channels ready.")
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
        msg_id = self._client.kernel_info()

        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: Waiting for kernel to be ready with msg_id {msg_id}...")

        start = time.monotonic()
        while True:
            try:
                msg = self._client.get_shell_msg(timeout=0.2)  # type: ignore[union-attr]
                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: Received message while waiting for kernel to be ready: {msg}")
                if msg["msg_type"] == "kernel_info_reply" and msg["parent_header"].get("msg_id") == msg_id:
                    return True
            except queue.Empty:
                pass

            if time.monotonic() - start > timeout:
                raise TimeoutError("Kernel did not become ready within the specified timeout.")

    def stop_channels(self):
        self._client.stop_channels()

    def get_kernel_info(self) -> dict:
        """Returns a dictionary with information about the Jupyter kernel."""
        msg_id = self._client.kernel_info()
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {msg_id = }")

        shell_msg = self._client.get_shell_msg(timeout=self._timeout)  # type: ignore[union-attr]
        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {shell_msg = }")

        return shell_msg["content"]

    # Channel proxy methods ------------------------------

    def get_shell_msg(self, *args, **kwargs):
        """Get a message from the shell channel"""
        return self._client.get_shell_msg(*args, **kwargs)  # type: ignore[union-attr]

    def get_iopub_msg(self, *args, **kwargs):
        """Get a message from the iopub channel"""
        return self._client.get_iopub_msg(*args, **kwargs)  # type: ignore[union-attr]

    def get_stdin_msg(self, *args, **kwargs):
        """Get a message from the stdin channel"""
        return self._client.get_stdin_msg(*args, **kwargs)  # type: ignore[union-attr]

    def get_control_msg(self, *args, **kwargs):
        """Get a message from the control channel"""
        return self._client.get_control_msg(*args, **kwargs)  # type: ignore[union-attr]

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
        reply = None
        saw_idle = False
        reply_received_at = None

        while True:
            try:
                io_msg = self._client.get_iopub_msg(timeout=self._timeout)  # type: ignore[union-attr]
                io_msg_type = io_msg["msg_type"]
                io_msg_content = io_msg["content"]
                io_parent_msg_id = io_msg.get("parent_header", {}).get("msg_id")

                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: io_msg = {io_msg}")
                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: io_msg_type = {io_msg_type}")
                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: io_msg_content = {io_msg_content}")

                if io_msg_type != "iopub_welcome" and io_parent_msg_id != msg_id:
                    continue

                if io_msg_type == "status":
                    if io_msg_content["execution_state"] == "idle":
                        saw_idle = True
                        if VERBOSE_DEBUG:
                            LOGGER.debug(f"{id(self)}: Execution State is Idle, terminating...")
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
                    data = io_msg_content.get("data", {})
                    text = data.get("text/plain")
                    if text is not None:
                        output.append(str(text).rstrip())
                elif io_msg_type == "iopub_welcome":
                    ...  # ignore this message type
                else:
                    LOGGER.warning(f"{id(self)}: Unknown io_msg_type: {io_msg_type}")
            except queue.Empty:
                if VERBOSE_DEBUG:
                    LOGGER.debug(f"{id(self)}: IOPub timed out while waiting for execution to complete; continuing")

            try:
                shell_msg = self._client.get_shell_msg(timeout=0.05)  # type: ignore[union-attr]
                if shell_msg["msg_type"] == "execute_reply" and shell_msg["parent_header"].get("msg_id") == msg_id:
                    reply = shell_msg
                    if reply_received_at is None:
                        reply_received_at = time.monotonic()
            except queue.Empty:
                pass

            if reply is not None and saw_idle:
                break

            # In rare cases, idle can be delayed or dropped; once we have the matching
            # execute_reply, don't block forever waiting for idle.
            if reply is not None and reply_received_at is not None:
                if time.monotonic() - reply_received_at > self._timeout:
                    if VERBOSE_DEBUG:
                        LOGGER.debug(f"{id(self)}: Execute reply received but no idle status observed; proceeding")
                        LOGGER.debug(f"{id(self)}: {reply = }")
                    break

        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {output = }")

        if reply is None:
            raise TimeoutError("Did not receive execute_reply for the submitted snippet.")

        if VERBOSE_DEBUG:
            LOGGER.debug(f"{id(self)}: {type(reply) = }")
            LOGGER.debug(f"{id(self)}: {reply = }")
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
