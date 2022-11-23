# Roadmap for the GUI Executor

This page will keep track of the features that we plan to implement in the future. The items will be ticked off when the feature is implemented.

GUI
  - [x] Allow sub-packages with their own task groups and organise them in TABs task view
  - [ ] Implement dark mode
  - [ ] There shall be a Preferences dailog to tune the behaviour of the GUI, e.g. toggle dark mode, set default timeout interval for recurring tasks, ....
  
Execution of tasks
  - [x] Tasks shall execute as a code snippet in a Jupyter kernel
  - [x] Tasks shall execute as a script in its own Python interpreter
  - [x] Tasks shall execute as a GUI script to show plots and tables
  - [x] It shall be possible to stop the execution of a task at all times

Logging
  - [x] The log shall contain all tasks that were executed with their start time and duration
  - [ ] It shall be possible to send logging information to a remote process using plain unix sockets or ZeroMQ
  - [ ] The log shall contain error information when a task execution failed

Documentation
  - [ ] Document environment variables and where they are used
  - [ ] Document special variables UI_TAB_ORDER, UI_TAB_DISPLAY_NAME, UI_TASK_DISPLAY_NAME
