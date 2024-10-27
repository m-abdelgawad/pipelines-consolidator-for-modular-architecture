"""
File utility module.

This module provides utility functions for file path manipulations,
such as obtaining the caller's file path and directory path.
"""

import os
import inspect


def caller_file_path():
    """
    Get the absolute path of the caller module file.

    Returns:
        str: The absolute file path of the caller module.
    """
    # Get the filename of the caller module from the stack
    return inspect.stack()[1].filename


def caller_dir_path():
    """
    Get the absolute directory path of the caller module file.

    Returns:
        str: The absolute directory path of the caller module.
    """
    # Get the filename of the caller module from the stack
    caller_abs_path = inspect.stack()[1].filename
    # Get the directory name from the absolute path
    return os.path.dirname(caller_abs_path)


def read(path):
    """
    Read the content of a file.

    Args:
        path (str): The file path to read.

    Returns:
        str: The content of the file.
    """
    with open(path, 'r') as file:
        return file.read()


if __name__ == "__main__":
    # If the module is run directly, print the caller file path
    print(caller_file_path())
