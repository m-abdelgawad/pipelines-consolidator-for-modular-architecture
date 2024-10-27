"""
GitLab API module.

This module contains the `GitLabAPI` class for interacting with GitLab.

API Endpoints Used:
- GET `/api/v4/projects/:id/repository/files/:file_path/raw?ref=:branch`: Fetch raw file content from a repository.

The `GitLabAPI` class provides methods to fetch Jenkinsfile content from GitLab repositories,
check for modularity in Jenkinsfiles, and parse shared libraries and module names.

"""

import requests
import re
from urllib3.exceptions import InsecureRequestWarning
import logging

# Import logger
log = logging.getLogger(__name__)

# Disable warnings related to insecure SSL requests
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class GitLabAPI:
    """
    Class to interact with GitLab API.

    Attributes:
        gitlab_private_token (str): The private token for authenticating with the GitLab API.

    Methods:
        convert_scm_url(scm_url): Converts an SCM URL to HTTPS format.
        get_jenkinsfile_content(scm_url, jenkinsfile_path, branch_specifier, job_name):
            Fetches the Jenkinsfile content from the GitLab repository.
        check_modularity(jenkinsfile_content): Checks if the Jenkinsfile is modular.
        parse_shared_library(jenkinsfile_content): Parses the shared library from the Jenkinsfile content.
        parse_module_name(jenkinsfile_content): Parses the module name from the Jenkinsfile content.

    """
    def __init__(self, gitlab_private_token):
        """
        Initialize GitLabAPI with the private token.

        Args:
            gitlab_private_token (str): The private token for authenticating with GitLab API.
        """
        self.gitlab_private_token = gitlab_private_token

    def convert_scm_url(self, scm_url):
        """
        Convert SCM URL to https:// format if necessary.

        Args:
            scm_url (str): The original SCM URL.

        Returns:
            str: The converted SCM URL in https:// format.

        Example:
            - Converts 'git@domain.com:group/project.git' to 'https://domain.com/group/project.git'
        """
        # If the URL already starts with https://, return it as is
        if scm_url.startswith("https://"):
            return scm_url
        # Convert git@ or git:// URLs to https:// format
        return re.sub(r'(?:git@)?(.*?):', r'https://\1/', scm_url)

    def get_jenkinsfile_content(
        self, scm_url, jenkinsfile_path, branch_specifier, job_name
    ):
        """
        Fetch the Jenkinsfile content from GitLab.

        Args:
            scm_url (str): The SCM URL of the GitLab repository.
            jenkinsfile_path (str): The path to the Jenkinsfile in the repository.
            branch_specifier (str): The branch name or pattern.
            job_name (str): The name of the Jenkins job.

        Returns:
            str or None: The content of the Jenkinsfile if fetched successfully,
                         or a string indicating the error (e.g., 'Project Not Found'),
                         or None if not found.

        GitLab API Endpoint Used:
            - GET `/api/v4/projects/:id/repository/files/:file_path/raw?ref=:branch`

        The function constructs the API URL based on the SCM URL and attempts to fetch the Jenkinsfile
        content from the specified branch.

        """
        if scm_url == "NA" or jenkinsfile_path == "NA":
            return None

        # Handle branch specifiers; if '**' or 'Any', try default branches
        if branch_specifier in ["**", "Any"]:
            branches_to_try = ["main", "master"]
        else:
            # Remove any wildcards or patterns from branch specifier
            branches_to_try = [branch_specifier.replace("*/", "")]

        # Encode slashes in the Jenkinsfile path for GitLab API
        jenkinsfile_path_encoded = jenkinsfile_path.replace("/", "%2F")

        for branch in branches_to_try:
            # Extract project path from SCM URL
            if scm_url.endswith(".git"):
                # Pattern to extract project path from SCM URL ending with .git
                pattern = r'https://git\.org-country\.internal\.replace-organization-name\.com/(.*)\.git'
            else:
                # Pattern for SCM URLs without .git suffix
                pattern = r'https://git\.org-country\.internal\.replace-organization-name\.com/(.*)'

            # Extract the project path
            project_path = re.sub(pattern, r'\1', scm_url)

            # Encode slashes in the project path for the GitLab API
            project_path_encoded = project_path.replace('/', '%2F')

            # Construct the Jenkinsfile API URL
            jenkinsfile_url = (
                f"https://git.org-country.internal.replace-organization-name.com/api/v4/projects/"
                f"{project_path_encoded}/repository/files/"
                f"{jenkinsfile_path_encoded}/raw?ref={branch}"
            )

            # Send GET request to fetch the Jenkinsfile content
            response = requests.get(
                jenkinsfile_url,
                headers={"Private-Token": self.gitlab_private_token},
                verify=False
            )

            # Check if the response is successful
            if response.status_code == 200:
                # Return the Jenkinsfile content
                return response.text
            else:
                # Log detailed information on failed fetch
                log.error(f"""Failed to fetch Jenkinsfile for job '{job_name}'
                          - Git URL: {scm_url}
                          - Branch: {branch}
                          - Jenkinsfile Path: {jenkinsfile_path}
                          - Request URL: {jenkinsfile_url}
                          - Response Code: {response.status_code}
                          - Response Content: {response.text}""")

                # Handle specific error messages in the response
                if "Project Not Found" in response.text:
                    return "Project Not Found"
                elif "File Not Found" in response.text:
                    return "Jenkinsfile Not Found"
                elif "Commit Not Found" in response.text:
                    return "Branch Not Found"

        # If none of the branches resulted in a successful fetch
        return None

    def check_modularity(self, jenkinsfile_content):
        """
        Check if the Jenkinsfile is modular by inspecting its content.

        Args:
            jenkinsfile_content (str): The content of the Jenkinsfile.

        Returns:
            bool or str: Returns True if the Jenkinsfile is modular,
                         False if not modular,
                         or a string message if Jenkinsfile content is invalid.

        """
        if jenkinsfile_content is None:
            return "Failed to fetch Jenkinsfile"
        elif "cicd-modular-library" in jenkinsfile_content:
            return True
        else:
            return False

    def parse_shared_library(self, jenkinsfile_content):
        """
        Parse the shared library used in the Jenkinsfile.

        Args:
            jenkinsfile_content (str): The content of the Jenkinsfile.

        Returns:
            str: The name of the shared library if found, otherwise 'No Shared Library'.

        The function looks for the @Library directive in the Jenkinsfile and extracts
        the shared library names used, excluding 'cicd-modular-library'.

        """
        # Check if jenkinsfile_content is a valid string before proceeding
        if not isinstance(jenkinsfile_content, str):
            # Log a warning and return default value
            log.warning("Invalid Jenkinsfile content: Expected a string.")
            log.warning("Jenkinsfile content: {}".format(jenkinsfile_content))
            return "No Shared Library"

        # Modify the regular expression to correctly match libraries
        library_match = re.search(r"@Library\(\['([^\]]+?)'\]\)_", jenkinsfile_content)

        if library_match:
            # Split the libraries by comma
            libraries = library_match.group(1).split(',')
            # Remove leading and trailing whitespaces and exclude 'cicd-modular-library'
            libraries = [lib.strip() for lib in libraries if lib.strip() != 'cicd-modular-library']
            # Get the first shared library name if available
            shared_library = libraries[0].strip("'") if libraries else "No Shared Library"
        else:
            shared_library = "No Shared Library"

        log.info("Shared library is: {}".format(shared_library))

        return shared_library

    def parse_module_name(self, jenkinsfile_content):
        """
        Parse the module name from the Jenkinsfile content.

        Args:
            jenkinsfile_content (str): The content of the Jenkinsfile.

        Returns:
            str: The module name if found, otherwise 'No Module Detected'.

        The function detects the first function call that resembles a module call
        (e.g., BigDataGenericPipeline(...)) and returns the module name, ignoring the @Library directive.

        """
        # Check if jenkinsfile_content is a valid string before proceeding
        if not isinstance(jenkinsfile_content, str):
            # Log a warning and return default value
            log.warning("Invalid Jenkinsfile content: Expected a string.")
            log.warning("Jenkinsfile content: {}".format(jenkinsfile_content))
            return "No Module Detected"

        # Ensure we skip the @Library directive and only detect actual module function calls
        # Look for function call patterns but avoid matching @Library
        module_match = re.search(r'^\s*(\w+)\s*\(', jenkinsfile_content, re.MULTILINE)

        if module_match and module_match.group(1) != 'Library':
            # Return the module name found (e.g., BigDataGenericPipeline)
            module_name = module_match.group(1)
        else:
            # Return if no module is detected
            module_name = "No Module Detected"

        log.info("Detected module name: '{}'".format(module_name))

        return module_name
