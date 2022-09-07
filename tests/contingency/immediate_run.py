from pathlib import Path

from gui_executor.exec import exec_ui

HERE = Path(__file__).parent.resolve()
ICON_PATH = HERE / "../../src/gui_executor/icons/"


@exec_ui(immediate_run=True, icons=(ICON_PATH / "stop.svg", ICON_PATH / "stop.svg"))
def stop_hexapod():
    import rich
    from rich.panel import Panel

    rich.print(Panel("Pressed the [red]STOP[/] button!"))
