from gui_executor.exec import exec_task


@exec_task()
def sleep_for_a_while(seconds: float = 10.0, verbose: bool = False) -> str:
    """A long-running task that simulates sleeping for a specified number of seconds.

    Args:
        seconds (float): The number of seconds to sleep. Default is 10.0 seconds.
        verbose (bool): Whether to print verbose output. Default is False.

    Returns:
        str: A message indicating how long the task slept.

    This function uses a loop to sleep in intervals, allowing it to be responsive to cancellation requests.
    """

    import time

    interval: float = 0.1
    elapsed: float = 0.0
    start_time = time.monotonic()

    print(f"Sleeping for {seconds} seconds...")
    while elapsed < seconds:
        time.sleep(interval)
        elapsed = time.monotonic() - start_time
        if verbose:
            print(f"Elapsed time: {elapsed:.2f} seconds", flush=True)

    return f"Slept for {seconds} seconds."
