import pathlib
import time
from gui_executor.exec import exec_ui

UI_MODULE_DISPLAY_NAME = "Console Output"


@exec_ui(display_name="Returns output")
def generates_a_lot_of_return(n_paragraphs: int = 10):
    from lorem_text import lorem

    out1 = lorem.paragraphs(n_paragraphs)
    out2 = pathlib.Path(__file__).read_text()

    return out1, out2


@exec_ui(display_name="Prints output")
def generates_a_lot_of_output(n_paragraphs: int = 10):
    from lorem_text import lorem

    print(lorem.paragraphs(n_paragraphs), flush=True)
    print()
    print(pathlib.Path(__file__).read_text(), flush=True)


@exec_ui(display_name="Stress output stream")
def stress_output_stream(n_lines: int = 500, line_size: int = 120, report_every: int = 100):
    """
    Generate a high-volume stream of console output for performance testing.

    Note: Rich rendering + GUI updates are CPU-bound on the main thread, so expect ~10-30ms per line.
    Keep n_lines reasonable (<1000) to avoid freezing the GUI for extended periods.
    """
    payload = "X" * max(1, line_size)
    t0 = time.perf_counter()

    for idx in range(1, max(1, n_lines) + 1):
        print(f"[{idx:06d}] {payload}", flush=True)
        if report_every > 0 and idx % report_every == 0:
            elapsed = time.perf_counter() - t0
            print(f"-- progress: {idx}/{n_lines} lines in {elapsed:.2f}s", flush=True)

    elapsed = time.perf_counter() - t0
    print(f"-- completed: {n_lines} lines in {elapsed:.2f}s", flush=True)
    return {"n_lines": n_lines, "line_size": line_size, "elapsed_s": round(elapsed, 3)}
