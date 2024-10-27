"""
This project fetches Jenkins jobs, extracts information, and processes them to determine details
about the jobs such as pipeline type, SCM URL, modularity, last run time, etc., by interacting with
the Jenkins and GitLab APIs. The results are saved into a CSV file.

Usage:
    python main.py

Requirements:
    - YAML configuration file (config.yaml) containing Jenkins and GitLab credentials.
    - Appropriate packages installed (see requirements.txt).
"""

import os
import yaml
import traceback
from packages.file import file
from packages.logger import logger
from packages.jenkins.jenkins_api import JenkinsAPI
from packages.gitlab.gitlab_api import GitLabAPI
from packages.helpers.helpers import (
    is_older_than_three_months, save_to_csv
)

# Initialize logger
log = logger.get(app_name='logs', enable_logs_file=False)


def main():
    """
    Main function to execute the job processing.

    This function initializes the APIs, fetches jobs from Jenkins, processes each job
    by fetching additional details from Jenkins and GitLab, and saves the results to a CSV file.
    """
    # Log the start of the program
    log.info('Start program execution')

    # Get the absolute path of the project directory
    project_abs_path = file.caller_dir_path()
    log.debug('Project path is: {}'.format(project_abs_path))

    # Load configurations from the config.yaml file
    config_path = os.path.join(project_abs_path, 'config.yaml')
    with open(config_path) as config_file:
        config = yaml.safe_load(config_file)

    # Extract Jenkins and GitLab configurations
    jenkins_url = config['jenkins']['url']
    username = config['jenkins']['username']
    api_token = config['jenkins']['api_token']
    gitlab_private_token = config['gitlab']['private_token']

    # Initialize Jenkins API client with URL, username, and API token
    jenkins_api = JenkinsAPI(jenkins_url, username, api_token)

    # Initialize GitLab API client with private token
    gitlab_api = GitLabAPI(gitlab_private_token)

    # Construct Jenkins API endpoint URL to fetch jobs
    base_url = (
        f"{jenkins_url}/api/json?tree=jobs[name,url,jobs[name,url]]"
    )

    # Fetch all jobs from Jenkins using the API client
    jobs = jenkins_api.fetch_jobs(base_url)

    # Initialize list to hold processed job data
    processed_jobs = []

    # Get the total number of jobs fetched
    total_jobs = len(jobs)

    # Iterate over each job and process it
    for index, (job_name, current_path, job_url) in enumerate(jobs, start=1):
        print(f"Processing {index} out of {total_jobs} jobs...")

        # Fetch the pipeline type (e.g., Pipeline Script, Pipeline Script from SCM)
        pipeline_type = jenkins_api.get_pipeline_type(job_url)

        # Fetch the SCM URL (e.g., Git repository URL)
        scm_url = jenkins_api.get_scm_url(job_url)

        # Convert SCM URL to a standard format (e.g., from git@... to https://...)
        scm_url = gitlab_api.convert_scm_url(scm_url)

        # Fetch the Jenkinsfile path from the job configuration
        jenkinsfile_path = jenkins_api.get_jenkinsfile_path(job_url)

        # Fetch the branch specifier (e.g., master, main, etc.) from the job configuration
        branch_specifier = jenkins_api.get_branch_specifier(job_url)

        # Initialize variables for shared library and module name
        shared_library = "NA"
        module_name = "NA"

        # Determine if the Jenkinsfile is modular or not
        if pipeline_type in ["Pipeline Script", "Unknown or not a Pipeline job"]:
            # If the pipeline type is "Pipeline Script" or unknown, it's not modular
            is_modular = False
        else:
            # Fetch the Jenkinsfile content from GitLab
            jenkinsfile_content = gitlab_api.get_jenkinsfile_content(
                scm_url, jenkinsfile_path, branch_specifier, job_name
            )

            # Check if the Jenkinsfile uses the modular pipeline approach
            is_modular = gitlab_api.check_modularity(jenkinsfile_content)

            if is_modular:
                # Parse the shared library used in the Jenkinsfile
                shared_library = gitlab_api.parse_shared_library(jenkinsfile_content)
                if shared_library == "No Shared Library":
                    module_name = "NA"
                else:
                    # Parse the module name from the Jenkinsfile content
                    module_name = gitlab_api.parse_module_name(jenkinsfile_content)

        # Extract the team name from the job path (assuming the first part is the team)
        team = current_path.split(" -> ")[0]

        # Fetch the last run date of the job
        last_run = jenkins_api.fetch_last_run(job_url)

        # Check if the last run is older than 3 months
        if last_run is None:
            # If there is no last run, set last run string to "No Runs" and mark as older
            last_run_str = "No Runs"
            older_than_three_months = True
        else:
            # Format the last run datetime as a string
            last_run_str = last_run.strftime("%Y-%m-%d %H:%M:%S")
            # Determine if the last run is older than three months
            older_than_three_months = is_older_than_three_months(last_run)

        # Append the processed job data to the list
        processed_jobs.append((
            job_name, current_path, job_url, team, pipeline_type,
            scm_url, jenkinsfile_path, branch_specifier, is_modular,
            shared_library, module_name, last_run_str, older_than_three_months
        ))

    # Save the processed jobs data to a CSV file
    save_to_csv(processed_jobs)

    # Log the end of the program
    log.info('Finished program execution')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        # Log any exceptions that occur during execution
        log.error(e)
        log.error('Error Traceback: \n {0}'.format(traceback.format_exc()))
