from pathlib import Path

from gui_executor.config import load_config
from gui_executor.kernel import MyKernel
from gui_executor.utils import remove_ansi_escape

HERE = Path(__file__).parent.resolve()


def test_print_sys_path_as_script():

    config = load_config(HERE / "data/snippets.yaml")

    cmd = config.get_command_for_snippet("print sys.path script")

    cmd.execute()

    out = cmd.get_output()

    print()
    print(f"*****\n{out = }\n*****")

    assert "Python.framework" in remove_ansi_escape(out)
    assert "Python.framework" in out


def test_print_sys_path_as_snippet():

    config = load_config(HERE / "data/snippets.yaml")

    cmd = config.get_command_for_snippet("print sys.path code")

    cmd.execute()

    out = cmd.get_output()

    print()
    print(f"*****\n{out = }\n*****")

    assert "Python.framework" in remove_ansi_escape(out)
    assert "Python.framework" in out


def test_running_the_same_kernel():

    config = load_config(HERE / "data/snippets.yaml")

    cmd1 = config.get_command_for_snippet("first-script")
    cmd2 = config.get_command_for_snippet("second-script")

    kernel = MyKernel()

    cmd1.execute(kernel=kernel)
    cmd2.execute(kernel=kernel)

    assert cmd2.get_output() == '42'
