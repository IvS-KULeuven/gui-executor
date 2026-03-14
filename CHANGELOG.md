# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.22.0] - 2026-03-14

- Upgrade API and messages for Jupyter client and server. The following changes have been implemented to handle the latest version of the protocol 5.5, that was shipped with jupyter-client 8.8.0:

  - handle the `iopub_welcome` message which is a new message type sent by the kernel to a client when it first connects to the IOPub channel. It was introduced to address a race condition problem where the client, connected to the IOPub channel mid-session, had no way of knowing what state the kernel was in or whether it had missed important messages. Clients also couldn't reliably know when their subscription was active and ready to receive messages.

  - in the newer jupyter_client, the signature of the `get_iopub_msg` and `get_shell_msg` methods changed and `msg_id` is no longer a valid argument. Filtering on `msg_id` (messages that belong to a certain execution) is now done in the loop body.

Other changes are not blocking and can be implemented later when needed.

## 0.21.3 - 2026-03-13

- Fix a hang of the GUI Executor after GUI startup and after the kernel has started up. The problem was a no-op in the handler of the queue.Empty (occurs after a timeout). Fixed by breaking out of the loop when the message timed out.



[Unreleased]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.22.0...HEAD
[0.22.0]: https://github.com/IvS-KULeuven/gui-executor/compare/v0.21.3...v0.22.0
