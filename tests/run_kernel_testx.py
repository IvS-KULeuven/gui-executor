"""
Script to test the Jupyter kernel.

Run this script as (the trailing x is to prevent pytest from picking up this file):

  $ python src/tests/run_kernel_testx.py

"""
import contextlib
import queue
import textwrap
import time

from rich.console import Console
from gui_executor.kernel import MyKernel

console = Console()

kernel = MyKernel()

snippet = textwrap.dedent(
    """
    import time

    print("starting...", flush=True)
    
    time.sleep(5.0)
    
    for idx in range(5):
        time.sleep(1.0)
        print(f"Running step {idx}...", flush=True)
    
    raise RuntimeError("Function was aborted!")
    
    rc = input("Continue? [Y/n]")
    # rc = input()  # prompt will be empty, still input_request is sent
    print(f"{rc = }")
    if rc.lower() == 'n':
        print("Sleeping for five more seconds...")
        time.sleep(5.0)
    
    print("finished!", flush=True)

""")

msg_id = kernel.client.execute(snippet, allow_stdin=True)

io_msg = kernel.client.get_iopub_msg(timeout=1.0)
console.log(io_msg)

io_msg_content = io_msg['content']  # execution_state should be 'busy'

while True:
    # with contextlib.suppress(queue.Empty):
    try:
        io_msg = kernel.client.get_iopub_msg(timeout=1.0)
        console.log(io_msg)

        io_msg_content = io_msg['content']

        if io_msg['msg_type'] == 'stream':
            if 'text' in io_msg_content:
                text = io_msg_content['text'].rstrip()
                console.log(f"[red]{text}[/red]")
        elif io_msg['msg_type'] == 'status':
            if io_msg_content['execution_state'] == 'idle':
                console.log("Execution State is Idle, terminating...")
                break

    except queue.Empty:
        with contextlib.suppress(queue.Empty):
            in_msg = kernel.client.get_stdin_msg(timeout=0.1)
            console.log(in_msg)

            if in_msg['msg_type'] == 'input_request':
                in_msg_content = in_msg['content']

                if "Continue?" in in_msg_content['prompt']:
                    console.log("[red]We got an input request, sending 'Y'.[/red]")
                    time.sleep(5.0)
                    kernel.client.input('n')

msg = kernel.client.get_shell_msg(msg_id)
console.log(msg)

msg_id = kernel.client.shutdown()
del kernel
