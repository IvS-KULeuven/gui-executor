import argparse
import time


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--duration",
        dest="duration",
        type=int,
        action="store",
        help="How long shall the command take, i.e. sleep(duration).",
    )
    return parser.parse_args()


def main():

    args = parse_arguments()

    duration = args.duration or 10  # wait 10s by default

    # Make sure the output is flushed properly, otherwise the asynchronous execution will
    # not be able to get the intermediate output.

    print(f"Starting a sleep({duration})", end='', flush=True)
    for _ in range(duration):
        time.sleep(1.0)
        print(".", end='', flush=True)
    print()
    print("Finished sleeping.")


if __name__ == "__main__":
    main()
