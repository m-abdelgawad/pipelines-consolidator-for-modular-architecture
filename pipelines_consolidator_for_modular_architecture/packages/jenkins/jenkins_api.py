"""
Jenkins API module.

This module contains the `JenkinsAPI` class for interacting with Jenkins.

API Endpoints Used:
- GET `/crumbIssuer/api/json`: Fetch the Jenkins crumb for CSRF protection.
- GET `/api/json?tree=jobs[name,url,jobs[name,url]]`: Fetch jobs with their names and URLs.
- GET `/lastBuild/api/json`: Fetch details of the last build of a job.
- GET `/config.xml`: Fetch the configuration XML of a job.

The `JenkinsAPI` class provides methods to fetch jobs, job configurations, last run dates,
pipeline types, SCM URLs, Jenkinsfile paths, and branch specifiers from Jenkins.

"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# Disable warnings related to insecure SSL requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class JenkinsAPI:
    """
    Class to interact with Jenkins API.

    Attributes:
        jenkins_url (str): The base URL of the Jenkins server.
        username (str): The username for authentication.
        api_token (str): The API token or password for authentication.
        crumb (str): The Jenkins crumb for CSRF protection.

    Methods:
        get_crumb(): Fetches the Jenkins crumb for CSRF protection.
        fetch_jobs(api_url, parent_path): Recursively fetches all Jenkins jobs.
        fetch_last_run(job_url): Fetches the last run timestamp of a job.
        get_pipeline_type(job_url): Determines the pipeline type of a job.
        get_scm_url(job_url): Fetches the SCM URL from the job configuration.
        get_jenkinsfile_path(job_url): Fetches the Jenkinsfile path from the job configuration.
        get_branch_specifier(job_url): Fetches the branch specifier from the job configuration.

    """
    def __init__(self, jenkins_url, username, api_token):
        """
        Initialize JenkinsAPI with URL, username, and API token.

        Args:
            jenkins_url (str): The base URL of the Jenkins server.
            username (str): The username for authentication.
            api_token (str): The API token or password for authentication.

        """
        self.jenkins_url = jenkins_url
        self.username = username
        self.api_token = api_token
        self.crumb = self.get_crumb()

    def get_crumb(self):
        """
        Fetch Jenkins crumb to prevent CSRF issues.

        Returns:
            str: The Jenkins crumb.

        Jenkins API Endpoint Used:
            - GET `/crumbIssuer/api/json`

        Raises:
            Exception: If the crumb cannot be fetched.

        """
        crumb_url = f"{self.jenkins_url}/crumbIssuer/api/json"
        print("[JenkinsAPI] Fetching Jenkins crumb...")

        # Send GET request to fetch the crumb
        response = requests.get(
            crumb_url, auth=(self.username, self.api_token), verify=False
        )

        # Check if the response is successful
        if response.status_code == 200:
            print("[JenkinsAPI] Successfully fetched crumb.")
            return response.json()["crumb"]
        else:
            raise Exception("Failed to fetch Jenkins crumb")

    def fetch_jobs(self, api_url, parent_path=""):
        """
        Recursively fetch all Jenkins jobs.

        Args:
            api_url (str): The Jenkins API URL to fetch jobs.
            parent_path (str): The hierarchical path of parent jobs (folders).

        Returns:
            list of tuples: A list containing tuples of (job_name, current_path, job_url).

        Jenkins API Endpoint Used:
            - GET `/api/json?tree=jobs[name,url,jobs[name,url]]`

        """
        # Send GET request to fetch jobs
        response = requests.get(
            api_url, auth=(self.username, self.api_token), verify=False
        )
        jobs_data = response.json()
        jobs = jobs_data.get("jobs", [])
        all_jobs = []

        # Iterate over each job in the jobs list
        for job in jobs:
            job_name = job["name"]
            job_url = job["url"]
            # Build the current path
            current_path = (
                f"{parent_path} -> {job_name}" if parent_path else job_name
            )

            # Check if the current job is a folder (has nested jobs)
            if "jobs" in job:
                # Recursively fetch nested jobs
                nested_api_url = (
                    f"{job_url}api/json?tree=jobs[name,url,jobs[name,url]]"
                )
                all_jobs.extend(
                    self.fetch_jobs(nested_api_url, current_path)
                )
            else:
                # Append job details for further processing
                all_jobs.append((job_name, current_path, job_url))

        return all_jobs

    def fetch_last_run(self, job_url):
        """
        Fetch the last run timestamp of a job from Jenkins.

        Args:
            job_url (str): The URL of the Jenkins job.

        Returns:
            datetime or None: The datetime of the last run if available, else None.

        Jenkins API Endpoint Used:
            - GET `/lastBuild/api/json`

        """
        last_build_url = f"{job_url}lastBuild/api/json"

        # Send GET request to fetch the last build data
        response = requests.get(
            last_build_url, auth=(self.username, self.api_token), verify=False
        )

        # Check if the response is successful
        if response.status_code == 200:
            build_data = response.json()
            # Extract the timestamp from the build data
            if 'timestamp' in build_data:
                timestamp_ms = build_data['timestamp']
                # Convert the timestamp from milliseconds to datetime
                last_run = datetime.fromtimestamp(timestamp_ms / 1000)
                return last_run
        return None

    def get_pipeline_type(self, job_url):
        """
        Determine the pipeline type of a Jenkins job by inspecting its config.

        Args:
            job_url (str): The URL of the Jenkins job.

        Returns:
            str: The pipeline type ('Pipeline Script', 'Pipeline Script from SCM',
                 or 'Unknown or not a Pipeline job').

        Jenkins API Endpoint Used:
            - GET `/config.xml`

        """
        config_url = f"{job_url}config.xml"

        # Send GET request to fetch the job configuration XML
        response = requests.get(
            config_url, auth=(self.username, self.api_token), verify=False
        )

        # Check if the response is successful
        if response.status_code == 200:
            config_xml = response.text
            root = ET.fromstring(config_xml)

            # Check for Pipeline Script
            if root.find(
                ".//definition[@class='org.jenkinsci.plugins.workflow.cps.CpsFlowDefinition']"
            ) is not None:
                return "Pipeline Script"
            # Check for Pipeline Script from SCM
            elif root.find(
                ".//definition[@class='org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition']"
            ) is not None:
                return "Pipeline Script from SCM"
        return "Unknown or not a Pipeline job"

    def get_scm_url(self, job_url):
        """
        Fetch SCM URL if the job is configured with a Pipeline Script from SCM.

        Args:
            job_url (str): The URL of the Jenkins job.

        Returns:
            str: The SCM URL (e.g., Git repository URL) if found, else 'NA'.

        Jenkins API Endpoint Used:
            - GET `/config.xml`

        """
        config_url = f"{job_url}config.xml"

        # Send GET request to fetch the job configuration XML
        response = requests.get(
            config_url, auth=(self.username, self.api_token), verify=False
        )

        # Check if the response is successful
        if response.status_code == 200:
            config_xml = response.text
            root = ET.fromstring(config_xml)

            # Find the SCM element
            scm = root.find(".//scm[@class='hudson.plugins.git.GitSCM']")
            if scm is not None:
                user_remote_configs = scm.find("userRemoteConfigs")
                if user_remote_configs is not None:
                    url_element = user_remote_configs.find(".//url")
                    if url_element is not None:
                        return url_element.text
        return "NA"

    def get_jenkinsfile_path(self, job_url):
        """
        Fetch the Jenkinsfile path configured in the pipeline.

        Args:
            job_url (str): The URL of the Jenkins job.

        Returns:
            str: The Jenkinsfile path if found, else 'NA'.

        Jenkins API Endpoint Used:
            - GET `/config.xml`

        """
        config_url = f"{job_url}config.xml"

        # Send GET request to fetch the job configuration XML
        response = requests.get(
            config_url, auth=(self.username, self.api_token), verify=False
        )

        # Check if the response is successful
        if response.status_code == 200:
            config_xml = response.text
            root = ET.fromstring(config_xml)

            # Find the scriptPath element
            script_path = root.find(".//definition/scriptPath")
            if script_path is not None:
                return script_path.text
        return "NA"

    def get_branch_specifier(self, job_url):
        """
        Fetch the branch specifier from the job configuration (Git branch).

        Args:
            job_url (str): The URL of the Jenkins job.

        Returns:
            str: The branch specifier (e.g., 'master', '**'), default is '**'.

        Jenkins API Endpoint Used:
            - GET `/config.xml`

        """
        config_url = f"{job_url}config.xml"

        # Send GET request to fetch the job configuration XML
        response = requests.get(
            config_url, auth=(self.username, self.api_token), verify=False
        )

        # Check if the response is successful
        if response.status_code == 200:
            config_xml = response.text
            root = ET.fromstring(config_xml)

            # Find the branches element
            branches = root.find(
                ".//scm[@class='hudson.plugins.git.GitSCM']/branches"
            )
            if branches is not None:
                branch_specifier = branches.find(".//name")
                if branch_specifier is not None:
                    return branch_specifier.text
        # If branch specifier is not found, return "**" to indicate wildcard
        return "**"
