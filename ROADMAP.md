# Roadmap for the GUI Executor

This page will keep track of the features that we plan to implement in the future. The items will be ticked off when the feature is implemented.

GUI
  - [x] Allow sub-packages with their own task groups and organise them in TABs task view
  - [x] Provide functionality to re-use tasks in other TABs and organised under different groups
  - [ ] Implement dark mode
  - [ ] There shall be a Preferences dailog to tune the behaviour of the GUI, e.g. toggle dark mode, set default timeout interval for recurring tasks, ....
  
Execution of tasks
  - [x] Tasks shall execute as a code snippet in a Jupyter kernel
  - [x] Tasks shall execute as a script in its own Python interpreter
  - [x] Tasks shall execute as a GUI script to show plots and tables
  - [x] It shall be possible to stop the execution of a task at all times
  - [ ] We need a clear strategy on handling concurrent tasks, e.g. output shall be in separate tabs in the output console.

Logging
  - [x] The log shall contain all tasks that were executed with their start time and duration
  - [ ] It shall be possible to send logging information to a remote process using plain unix sockets or ZeroMQ
  - [ ] The log shall contain error information when a task execution failed

Documentation
  - [ ] Document environment variables and where they are used, e.g. CUTELOG_HOST
  - [ ] Document special variables UI_TAB_ORDER, UI_TAB_DISPLAY_NAME, UI_TASK_DISPLAY_NAME

To Think About
  - [ ] What about two modes, a user mode and an expert mode. Tasks that are expert mode are not shown in the GUI until expert mode is selected. Expert mode can be selected in Settings (doesn't exist yet) or else ?
  - 
