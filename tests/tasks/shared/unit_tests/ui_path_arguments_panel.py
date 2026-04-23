from pathlib import Path

from gui_executor.exec import exec_ui, FileName, FilePath, Directory

UI_MODULE_DISPLAY_NAME = "Path-like Arguments"


@exec_ui(display_name="Select a folder")
def select_folder(location: Path):
    print(f"{location = }")


@exec_ui(display_name="Open File", file_filter={"filepath": "*.md"})
def open_file(
    filename: FileName = "README.md",
    filepath: FilePath = None,
    location: Directory = Path("/Users/rik/Documents/PyCharmProjects/gui-executor/"),
):
    """
    Test function for `FileName`, `FilePath`, and `Directory` annotations.

    For the `filepath` argument, a filter is added to allow only selection of "*.md".
    """
    print(f"{filename = }, {type(filename) = }")
    print(f"{filepath = }, {type(filepath) = }")
    print(f"{location = }, {type(location) = }")


@exec_ui(
    display_name="Select a specific file type",
    file_filter={
        "yaml_file": "YAML Files (*.yaml *.yml)",
        "md_file": "Markdown Files (*.md *.markdown)",
    },
)
def select_file(yaml_file: FilePath, md_file: Path):
    """
    Test function for file_filter.
    The `yaml_file` argument is of type `FilePath` and shall only allow YAML files.
    The `md_file` argument is of type `Path` and shall only allow Markdown files.
    """
    print(f"{yaml_file = }, {type(yaml_file) = }")
    print(f"{md_file = }, {type(md_file) = }")
