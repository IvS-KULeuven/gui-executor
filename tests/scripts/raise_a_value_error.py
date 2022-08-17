"""
This script will raise a ValueError if the --value argument is greater than 10.

The purpose of this script is to test the behaviour of the command execution when an exception is raised.
"""
import argparse
import time


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--value",
        dest="value",
        type=int,
        action="store",
        default=0,
        help="A value that can raise a ValueError when > 10.",
    )
    return parser.parse_args()


def main():

    args = parse_arguments()

    time.sleep(2.0)
    if args.value > 10:
        raise ValueError(f"Incorrect input received: {args.value}")


if __name__ == "__main__":
    main()
