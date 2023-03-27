import argparse
import logging
import os
import sys
from logging.handlers import SocketHandler
from pathlib import Path

from PyQt5.QtCore import QLockFile
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMessageBox

from gui_executor.utils import print_system_info
from .config import load_config
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
    parser.add_argument('--version', "-V", action="store_true", help='print the gui-executor version number and exit')
    parser.add_argument('--verbose', "-v", action="count",
                        help="print verbose information, increased verbosity level with multiple occurrences")
    parser.add_argument('--location', help='location of the Python modules and scripts')
    parser.add_argument('--cmd-log', help='location of the command log files')
    parser.add_argument('--module-path', action="append", help='module path of the Python modules and scripts')
    parser.add_argument('--kernel-name',
                        help="the kernel that will be started by default, python3 if not given")
    parser.add_argument('--config', help='a YAML file that configures the executor')
    parser.add_argument('--logo', help='path to logo PNG or SVG file')
    parser.add_argument('--app-name', help='the name of the GUI app, will go in the window title')
    parser.add_argument('--debug', '-d', action="store_true", help="set debugging mode")
    parser.add_argument('--single', action="store_true", help='the UI can be started only once (instead of multiple times)')

    args = parser.parse_args()

    verbosity = 0 if args.verbose is None else args.verbose
    kernel_name = args.kernel_name or "python3"
    module_path_list = args.module_path

    single = 1 if args.single is None else args.single
    lock_file = QLockFile(str(Path(f"~/{args.app_name or 'GUI executor'}.app.lock").expanduser())) if single else None

    if args.version:
        from .__version__ import __version__ as version
        print(f"gui-executor {version=}")
        if verbosity:
            print_system_info()
        sys.exit(0)

    if args.debug:
        from gui_executor import view, client, kernel
        view.DEBUG = True
        client.DEBUG = True
        kernel.DEBUG = True

    log = logging.getLogger('gui-executor')
    log.setLevel(1 if args.debug else logging.WARNING)  # to send all records to cutelog
    host = os.environ.get("CUTELOG_HOST", '127.0.0.1')
    socket_handler = SocketHandler(host, 19996)  # default listening address
    log.addHandler(socket_handler)

    # We have only implemented the --module-path option for now

    if args.module_path is None:
        print("You need to provide at least one --module-path option.")
        parser.print_help()
        return

    if args.config:
        load_config(args.config)

    app = QApplication([])
    app.setWindowIcon(QIcon(args.logo or str(HERE / "icons/tasks.svg")))

    # Enter here when either:
    #   - the UI is allowed to be opened multiple times
    #   - the UI is not allowed to be started multiple times, but it is the first instance

    if not single or lock_file.tryLock(100):

        model = Model(module_path_list)
        view = View(model,
                    app_name=args.app_name or "GUI Executor",
                    cmd_log=args.cmd_log, verbosity=verbosity, kernel_name=kernel_name)

        view.show()

        return app.exec()

    # You try to open the UI multiple times, even though this is not allowed

    else:
        error_message = QMessageBox()
        error_message.setIcon(QMessageBox.Warning)
        error_message.setWindowTitle("Error")
        error_message.setText(f"The {args.app_name or 'GUI executor'} application is already running!")
        error_message.setStandardButtons(QMessageBox.Ok)

        return error_message.exec()


if __name__ == "__main__":
    sys.exit(main())
