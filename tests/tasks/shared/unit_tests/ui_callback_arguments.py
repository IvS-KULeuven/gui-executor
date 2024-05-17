import random
from enum import IntEnum

from gui_executor.exec import exec_ui
from gui_executor.utypes import Callback

UI_MODULE_DISPLAY_NAME = "Callback Arguments"


class Digit(IntEnum):
    ZERO = 0
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9


def int_enum():
    return Digit


def random_word():
    words = ("ONE", "TWO", "THREE", "FOUR", "FIVE")
    return random.choice(words)


def list_of_floats():
    return [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]


@exec_ui()
def random_callback(word: Callback(random_word, name="str")):
    print(f"A random word: {word}")


def default_digit() -> Digit:
    return Digit.EIGHT


@exec_ui()
def enum_callback(digit: Callback(int_enum, name="int", default=default_digit)):
    print(f"You selected {digit}")


def default_float() -> float:
    return 0.5


@exec_ui()
def list_callback(number: Callback(list_of_floats, name="float", default=default_float)):
    print(f"You selected {number}")


@exec_ui()
def list_callback_keyword(number: Callback(lambda: [None, 1, 2, 3], name="Bandpass colors") = None):
    print(f"You selected {number}")
