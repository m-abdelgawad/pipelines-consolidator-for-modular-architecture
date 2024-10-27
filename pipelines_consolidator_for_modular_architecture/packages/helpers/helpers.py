"""
Helper functions module.

This module contains helper functions used across the project, such as checking
if a date is older than three months and saving data to a CSV file.

Functions:
    is_older_than_three_months(last_run): Checks if a datetime is older than three months.
    save_to_csv(jobs, filename): Saves job data to a CSV file.

"""

import csv
from datetime import datetime, timedelta


def is_older_than_three_months(last_run):
    """
    Check if the last run is older than three months.

    Args:
        last_run (datetime): The datetime of the last run.

    Returns:
        bool or None: True if older than three months, False if not, None if last_run is None.

    """
    if last_run is None:
        return None
    # Calculate the date three months ago from today
    three_months_ago = datetime.now() - timedelta(days=90)
    return last_run < three_months_ago


def save_to_csv(jobs, filename="data/output/results.csv"):
    """
    Save the jobs information to a CSV file.

    Args:
        jobs (list of tuples): The list of job data to save.
        filename (str): The filename where to save the CSV data.

    Returns:
        None

    """
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        # Write header row
        writer.writerow([
            "job_name", "path", "job_url", "team", "pipeline_type", "scm_url",
            "jenkinsfile_path", "branch_specifier", "is_modular",
            "shared_library", "shared_library_module", "last_run", "Is_last_run_old"
        ])
        # Write job data rows
        for job in jobs:
            writer.writerow(job)
