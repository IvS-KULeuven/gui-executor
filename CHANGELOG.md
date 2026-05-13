# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.25.1] - 2026-05-13

### Changed

- Refactored `stringify_imports` and `stringify_var_name_checks` to accept an `indent` parameter for better formatting control in generated code snippets. See issue [#95](https://github.com/IvS-KULeuven/gui-executor/issues/95).

## [0.25.0] - 2026-04-23

### Added

- Added file filter support for file selection in UI functions.
- Added `.vscode/` to `.gitignore`.
- Added `tests/tasks/specific/output/convert.py` with a `convert_to_float` task used by the updated `test_run_func` test.

### Removed

- Removed the unused `command.py` module (`Command`, `ScriptCommand`, `SnippetCommand`, `AppCommand`, `CommandError`) and its associated tests (`test_command.py`, `test_executor.py`, `test_environment.py`) and test data files (`scripts.yaml`, `snippets.yaml`).
- Removed the unused `config.py` module (`ExecutorConfiguration`, `ConfigError`, `load_config`) and its associated tests (`test_config.py`) and test data file (`sample_config.yaml`).
- Removed the `--config` CLI option from `gui-executor` (was calling the now-removed `load_config`).
- Removed the `cutelog` socket log handler and its `CUTELOG_HOST` environment variable from `__main__.py`.
- Removed dead commented-out `VERBOSE_DEBUG` assignments in the `--debug` branch of `__main__.py`.

### Fixed

- Fixed incorrect log message in `MyClient.__init__`: was logging `type(self)` (always `MyClient`) instead of `type(self._client)` (the actual underlying kernel client type).
- Fixed import path for `KernelClient`: changed `from jupyter_client import KernelClient` to `from jupyter_client.client import KernelClient`.
- Fixed a debug log statement in `view._cast_arg` that was emitting unconditionally; it is now guarded by `if VERBOSE_DEBUG`.
- Fixed `test_file_selection.py`: replaced hardcoded absolute path with a portable `~/Desktop/` expansion, added proper assertions, and added a 1-second auto-close timer so the test does not hang.
- Fixed `test_gui_exec.py`: replaced stale references to the removed `contingency` module with `tasks.shared.unit_tests`; replaced the non-portable `test_end_observation` test with `test_run_func` that exercises the new `convert_to_float` task.

## [0.24.0] - 2026-04-22

### Added

- Added plain text and lightweight (ANSI colored) rendering modes to the console output panel. Plain Text mode is the new default; Lightweight mode renders Rich markup and ANSI escape sequences with colors and styling.
- Added a font selection dialog for the console output panel, accessible from the `View` menu and the console context menu.
- Added autosave feature for console output via the `--save-console-output <path>` command-line option. The file is truncated on startup and flushed continuously as plain text regardless of the active render mode.
- Added attention mode: setting the environment variable `GUI_EXECUTOR_ATTENTION_LABEL` draws a colored border around the application window and shows a permanent badge in the status bar. The color defaults to red (`#d62828`) and can be overridden with `GUI_EXECUTOR_ATTENTION_COLOR`. The fallback `GUI_EXECUTOR_ATTENTION_MODE` boolean flag is also supported.
- Anti-flicker improvement for recurring status-bar tasks: overlapping runs of the same task are now skipped, and redundant status bar writes (same text) are suppressed.

### Fixed

- Fixed `AttributeError` when interrupting the kernel: `interrupt_kernel` now safely checks whether a kernel and a running runnable are actually present before attempting to interrupt.
- Fixed the SourceCodeWindow: source code was no longer shown after a refactor; the window now centers the cursor on the function's first line.
- Suppressed a spurious `rich.print` dump of the `execute_reply` shell message that appeared in the terminal on GUI startup.

## [0.23.0] - 2026-03-28

### Added

- Added `DropdownList` user type: a dynamic list of dropdown (combo box) selectors. Each row presents a `QComboBox` populated from a provided list of choices, allowing tasks to accept a variable number of enum-style selections.
- Added documentation for `ListList` and `DropdownList` type hints.

## [0.22.3] - 2026-03-26

- Added QCheckBox support for boolean Callback return values. The CallbackWidget always rendered a QLineEdit for boolean callbacks, making it impossible to set False (bool of any non-empty string is True).

## [0.22.0] - 2026-03-14

- Upgrade API and messages for Jupyter client and server. The following changes have been implemented to handle the latest version of the protocol 5.5, that was shipped with jupyter-client 8.8.0:

  - handle the `iopub_welcome` message which is a new message type sent by the kernel to a client when it first connects to the IOPub channel. It was introduced to address a race condition problem where the client, connected to the IOPub channel mid-session, had no way of knowing what state the kernel was in or whether it had missed important messages. Clients also couldn't reliably know when their subscription was active and ready to receive messages.

  - in the newer jupyter_client, the signature of the `get_iopub_msg` and `get_shell_msg` methods changed and `msg_id` is no longer a valid argument. Filtering on `msg_id` (messages that belong to a certain execution) is now done in the loop body.

Other changes are not blocking and can be implemented later when needed.

## 0.21.3 - 2026-03-13

- Fix a hang of the GUI Executor after GUI startup and after the kernel has started up. The problem was a no-op in the handler of the queue.Empty (occurs after a timeout). Fixed by breaking out of the loop when the message timed out.



[Unreleased]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.25.1...HEAD
[0.25.1]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.25.0...v0.25.1
[0.25.0]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.24.0...v0.25.0
[0.24.0]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.23.0...v0.24.0
[0.23.0]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.22.4...v0.23.0
[0.22.3]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.22.0...v0.22.3
[0.22.0]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.21.3...v0.22.0
