"""
Logger utility module.

This module provides utility functions to set up a logger for the application,
including file logging with rotation and console logging.

Functions:
    setup_app_logger(logger_name, log_file_path): Sets up the application logger.
    create_log_file(app_name, parent_dir_path): Creates a log file with a timestamped name.
    get(app_name, enable_logs_file): Initializes and returns the logger.

"""

import os
import sys
import inspect
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler


def setup_app_logger(logger_name, log_file_path=None):
    """
    Set up the application logger with console and optional file handlers.

    Args:
        logger_name (str): The name of the logger.
        log_file_path (str or None): The file path to save logs, or None to disable file logging.

    Returns:
        logging.Logger: The configured logger instance.

    """
    # Create a logger
    logger = logging.getLogger(logger_name)

    # Set the level of logging
    logger.setLevel(logging.INFO)

    # Set the format of the log message
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set up the console log handler (stdout)
    log_handler = logging.StreamHandler(sys.stdout)
    log_handler.setFormatter(formatter)

    # Clear any previous handlers and add the console handler
    logger.handlers.clear()
    logger.addHandler(log_handler)

    # If a log file path is provided, set up file logging
    if log_file_path:
        # Set up a RotatingFileHandler to write logs to the file
        file_handler = RotatingFileHandler(
            filename=log_file_path, mode='a', maxBytes=5 * 1024 * 1024,
            backupCount=100, encoding='utf8', delay=False
        )
        file_handler.setFormatter(formatter)
        # Add the file handler to the logger
        logger.addHandler(file_handler)

    # Return the configured logger
    return logger


def create_log_file(app_name, parent_dir_path):
    """
    Create a log file with a timestamped name in the logs directory.

    Args:
        app_name (str): The name of the application or log file prefix.
        parent_dir_path (str): The parent directory where logs directory will be created.

    Returns:
        str: The full path to the created log file.

    """
    # Create logs folder if it does not exist
    logs_folder_path = os.path.join(parent_dir_path, 'logs')
    if not os.path.exists(logs_folder_path):
        os.makedirs(logs_folder_path)

    # Get current timestamp in specific format
    current_timestamp = datetime.now().strftime("%Y-%m-%d__%H-%M-%S")

    # Construct the log file name
    logs_file_name = f"{app_name}__{current_timestamp}.log"

    # Full path to the log file
    logs_file_path = os.path.join(logs_folder_path, logs_file_name)

    # Create the log file if it does not exist
    if not os.path.exists(logs_file_path):
        open(logs_file_path, 'w').close()

    return logs_file_path


def get(app_name='logs', enable_logs_file=True):
    """
    Initialize and return the application logger.

    Args:
        app_name (str): The name of the application or log file prefix.
        enable_logs_file (bool): Flag to enable or disable file logging.

    Returns:
        logging.Logger: The configured logger instance.

    """
    if enable_logs_file:
        # Get the absolute path of the caller module
        caller_abs_path = inspect.stack()[1].filename

        # Get the absolute path of the parent directory (assumed repo directory)
        repo_abs_path = os.path.dirname(os.path.dirname(caller_abs_path))

        # Create the log file
        logs_file_path = create_log_file(
            app_name=app_name, parent_dir_path=repo_abs_path
        )

        # Set up the logger with file logging
        logger = setup_app_logger(logger_name='', log_file_path=logs_file_path)
    else:
        # Set up the logger without file logging
        logger = setup_app_logger(logger_name='', log_file_path=None)

    # Return the logger
    return logger
