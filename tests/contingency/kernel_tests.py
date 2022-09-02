import time

from gui_executor.exec import exec_ui


@exec_ui()
def test_async_kernel_execution():
    """
    We are testing here if the kernel is executed immediately and  asynchronously.
    We have this function running for at least 15s and print output in between, every 2s.
    """

    for idx in range(20):
        time.sleep(1.0)
        if idx % 2 == 0:
            print(f"Running step {idx}...", flush=True)

    print("Finished!", flush=True)
