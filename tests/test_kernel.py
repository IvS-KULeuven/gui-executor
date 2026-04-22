import textwrap

import pytest
import rich

from gui_executor.kernel import MyKernel
from gui_executor.client import MyClient


@pytest.fixture(scope="module")
def kernel():
    kernel = MyKernel()
    client = MyClient(kernel)
    client.run_snippet("a = None")

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
    out = MyClient(kernel).run_snippet(snippet)
    print()
    print(f"*****\n{out}\n*****")
    assert "a = 44" in out
    assert "a = 52" in out
    assert "total = 52" in out


def test_kernel_is_alive(kernel):
    assert kernel.is_alive()


@pytest.mark.order(2)
def test_kernel_after_initialisation(kernel):
    out = MyClient(kernel).run_snippet("""print(f"{a = }")""")
    print()
    print(f"*****\n{out}\n*****")
    assert "a = 52" in out

    out = MyClient(kernel).run_snippet("a is not None")
    print()
    print(f"*****\n{out}\n*****")
    assert out == "True"


def test_get_kernel_specs(kernel):
    rich.print()

    specs = kernel.get_kernel_specs()

    assert "python3" in specs
    assert isinstance(specs, dict)

    rich.print(specs)


def test_run_snippet(kernel):
    print()

    snippet = textwrap.dedent("""
        import time

        print("starting...", flush=True, end="")
        time.sleep(1.0)
        print("finished!", flush=True)

    """)

    client = MyClient(kernel)
    out = client.run_snippet(snippet)

    assert "starting..." in out
    assert "finished!" in out
