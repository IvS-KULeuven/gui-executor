import textwrap

import pytest
import rich

from gui_executor.kernel import MyKernel


@pytest.fixture(scope="module")
def kernel():
    kernel = MyKernel()
    kernel.run_snippet("a = None")

    yield kernel

    del kernel  # explicitly shutdown the kernel


@pytest.mark.order(1)
def test_kernel_initialisation(kernel):

    snippet = textwrap.dedent("""\
        a = 42
        for _ in range(5):
            a += 2
            print(f"{a = }")
        print(f"total = {a}")
    """)
    out = kernel.run_snippet(snippet)
    print()
    print(f"*****\n{out}\n*****")
    assert "a = 44" in out
    assert "a = 52" in out
    assert "total = 52" in out


def test_kernel_is_alive(kernel):
    assert kernel.is_alive()


@pytest.mark.order(2)
def test_kernel_after_initialisation(kernel):
    out = kernel.run_snippet("""print(f"{a = }")""")
    print()
    print(f"*****\n{out}\n*****")
    assert "a = 52" in out

    out = kernel.run_snippet('a is not None')
    print()
    print(f"*****\n{out}\n*****")
    assert out == "True"


def test_kernel_info(kernel):

    rich.print()

    info = kernel.get_kernel_info()
    rich.print(info)

    specs = kernel.get_kernel_specs()
    rich.print(specs)


def test_run_snippet(kernel):

    print()

    snippet = textwrap.dedent("""
        import time
        
        print("starting...", flush=True, end="")
        time.sleep(5.0)
        print("finished!", flush=True)
        
    """)

    msg_id = kernel.client.execute(snippet)
    msg = kernel.client.get_shell_msg(msg_id)
    print(f"1 {'-'*20} {msg = }")

    io_msg = kernel.client.get_iopub_msg(timeout=1.0)
    io_msg_content = io_msg['content']
    print(f"2 {'-'*20} {io_msg_content = }")
