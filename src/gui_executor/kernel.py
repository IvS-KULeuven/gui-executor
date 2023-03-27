import logging
import textwrap

import jupyter_client.kernelspec
import rich
from executor import ExternalCommand
from executor import ExternalCommandFailed
from jupyter_client import KernelClient
from jupyter_client.manager import KernelManager
from rich import print
from rich.console import Console

LOGGER = logging.getLogger("gui-executor.kernel")
DEBUG = False


class KernelError(Exception):
    pass


def find_running_kernels():
    import psutil, datetime
    all_python = [proc for proc in psutil.process_iter() if "python" in proc.name().lower()]
    kernel_processes = [y for y in all_python for z in y.cmdline() if 'ipykernel' in z]
    datetime.datetime.fromtimestamp(kernel_processes[0].create_time()).strftime("%Y-%m-%d %H:%M:%S")

# TODO:
#    * Create a separate kernel and client class
#      For the kernel class, check if there is a need to re-connect to an existing kernel first.
#      For the client class, connect to the kernel with:
#
#        from jupyter_client import BlockingKernelClient
#
#        client = BlockingKernelClient()
#        client.load_connection_file('/Users/ebanner/Library/Jupyter/runtime/kernel-10962.json')
#        client.start_channels()
#
#    * see also
#      https://ipython.readthedocs.io/en/stable/development/wrapperkernels.html
#      https://github.com/ipython/ipykernel

class MyKernel:

    def __init__(self, name: str = "python3", startup_timeout: int = 60):
        self._kernel = KernelManager(kernel_name=name)
        self._kernel.start_kernel()
        self._startup_timeout = startup_timeout
        self._error = None

    def is_alive(self) -> bool:
        return self._kernel.is_alive()

    def shutdown(self):
        self._kernel.shutdown_kernel(now=True)

    def interrupt_kernel(self):
        self._kernel.interrupt_kernel()

    def get_client(self) -> KernelClient:
        return self._kernel.client()

    @staticmethod
    def get_kernel_specs():
        return jupyter_client.kernelspec.find_kernel_specs()

    def get_connection_file(self):
        return self._kernel.connection_file

    def get_connection_info(self):
        info = self._kernel.get_connection_info(session=True)
        info.update(
            dict(
                connection_file=self._kernel.connection_file,
                parent=self._kernel,
            )
        )
        return info

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


def do_test_my_kernel(name: str = "python3"):
    from gui_executor.client import MyClient
    from gui_executor.utils import Timer

    kernel = MyKernel(name=name)

    rich.print(kernel.get_kernel_specs())

    client = MyClient(kernel)
    client.connect()

    rich.print(client.get_kernel_info())

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

    console = Console(width=240)
    for snippet in snippets:
        if out := client.run_snippet(snippet):
            console.print(out)

    client.disconnect()

    with Timer("MyClient as context manager"):
        with MyClient(kernel) as client:
            info = client.get_kernel_info()


def start_qtconsole(kernel: MyKernel,
                    buffer_size: int = 5000,
                    console_height: int = 42, console_width: int = 128,
                    console_font: str = "Courier New",
                    verbosity: int = 0):
    connection_file = kernel.get_connection_file()
    cmd_line = (f"jupyter qtconsole --ConsoleWidget.buffer_size={buffer_size} "
                f"--ConsoleWidget.console_height={console_height} "
                f"--ConsoleWidget.console_width={console_width} "
                f"--ConsoleWidget.font_family='{console_font}' "
                f"--existing {connection_file} --log-level=INFO")

    if verbosity:
        print("Starting Jupyter Qt Console...")
        print(f"{cmd_line = }")

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
