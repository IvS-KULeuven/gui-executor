from gui_executor.exec import exec_ui


@exec_ui()
def a_function_with_failed_import():
    import non_existing_module

    print("This message should never be printed")
