import os


def hide_this_tab():
    """Hide the output TAB if the environment variable HIDE_OUTPUT_TAB exists and is not empty."""
    hide = os.environ.get('HIDE_OUTPUT_TAB', False)
    return hide


UI_TAB_HIDE = hide_this_tab
