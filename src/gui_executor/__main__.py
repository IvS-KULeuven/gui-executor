import argparse
import sys

from PyQt5.QtWidgets import QApplication
from executor import ExternalCommand
from .config import load_config
from .view import View
from .control import Control
from .model import Model


# EXAMPLE:
#   Use a function like this in your package and add it to the entry_points in the setup.py
#   Replace 'contingency' by a package that contains the scripts you want to execute from the GUI.
def contingency_ui():
    cmd = ExternalCommand("gui-executor --module-path contingency", asynchronous=True)
    cmd.start()


def main():

    parser = argparse.ArgumentParser(prog='gui-executor')
    parser.add_argument('--location', help='location of the Python modules and scripts')
    parser.add_argument('--module-path', help='module path of the Python modules and scripts')
    parser.add_argument('--config', help='a YAML file that configures the executor')

    args = parser.parse_args()

    print(f"{args = }")
    print(f"{args.location = }, {args.module_path = }")

    if args.config:
        load_config(args.config)

    app = QApplication([])

    view = View()
    model = Model(args.module_path)
    Control(view, model)

    view.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
