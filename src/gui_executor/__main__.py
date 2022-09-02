import argparse
import logging
import sys
from pathlib import Path

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from .config import load_config
from .control import Control
from .model import Model
from .view import View

HERE = Path(__file__).parent.resolve()

# EXAMPLE:
#   Use a function like this in your package '__init__' file and add it to the entry_points in the setup.py.
#   This function will load functions that are decorated with '@exec_ui' from all modules in 'camtest.contingency'
#   and dynamically create the GUI executor for them.
#
#     def contingency_ui():
#         cmd = ExternalCommand("gui-executor --module-path camtest.contingency", asynchronous=True)
#         cmd.start()
#
#   Replace 'camtest.contingency' by a package that contains the scripts you want to execute from the GUI.
#
#       entry_points={
#         "gui_scripts": [
#             "contingency_ui=camtest.contingency.__init__:contingency_ui",
#         ]
#     },


def main():

    parser = argparse.ArgumentParser(prog='gui-executor')
    parser.add_argument('--location', help='location of the Python modules and scripts')
    parser.add_argument('--module-path', help='module path of the Python modules and scripts')
    parser.add_argument('--config', help='a YAML file that configures the executor')
    parser.add_argument('--logo', help='path to logo PNG or SVG file')
    parser.add_argument('--app-name', help='the name of the GUI app, will go in the window title')
    parser.add_argument('--debug', '-d', action="store_true", help="set debugging mode")

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)

    # We have only implemented the --module-path option for now

    if args.module_path is None:
        print("You need to provide the --module-path option.")
        parser.print_help()
        return

    if args.config:
        load_config(args.config)

    app = QApplication([])
    app.setWindowIcon(QIcon(args.logo or str(HERE / "icons/tasks.svg")))

    view = View(args.app_name or "GUI Executor")
    model = Model(args.module_path)
    Control(view, model)

    view.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
