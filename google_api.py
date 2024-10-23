"""
google_api.py

This module provides functions to authenticate and interact with Google APIs, specifically focusing 
on Google Drive. It handles the OAuth2 flow, obtains user credentials, and creates a service object 
for interacting with Google Drive's API. 

Key Functions:
- `configure_browser`: Configures the browser to use for the OAuth2 flow.
- `request_credentials`: Requests credentials from the user by running the OAuth2 flow locally.
- `get_credentials`: Retrieves saved credentials from the token file or requests new credentials if needed.
- `create_service`: Creates a Google API service client for interacting with a specific API (e.g., Google Drive).

The module uses OAuth2 authentication via the Google API client library, saving credentials to a token 
file after initial authorization for subsequent use. It supports refreshing expired tokens automatically.

Constants:
- `CLIENT_SECRETS_FILE`: Path to the client secrets JSON file for OAuth2 authentication.
- `TOKEN_FILE`: Path to the token file where OAuth2 credentials are stored.
- `API_VERSION`: Version of the Google API to use (currently v3 for Google Drive).
- `API_SERVICES`: Dictionary containing API service names and corresponding scopes.

Dependencies:
- googleapiclient
- google-auth
- google-auth-oauthlib

Usage:
- Ensure that `client-secrets-file.json` is present in the same directory.
- Run the script to authorize access to the specified Google API services and perform API operations.

"""

import os
import sys
import platform
import webbrowser

from typing import Any
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Constants for client secrets and token files
CLIENT_SECRETS_FILE: str = "client-secrets-file.json"
TOKEN_FILE: str = "token.json"
API_VERSION: str = "v3"

# Define the API services and scopes needed for authentication
API_SERVICES: dict[str, dict[str, Any]] = {
    "drive": {
        "service_name": "drive",
        "scopes": [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.metadata"
        ]
    }
}


def configure_browser_old() -> None:
    """
    Configures the browser to be used during the OAuth2 flow for user authentication.

    This function registers Google Chrome as the default browser to handle the OAuth2
    process, allowing the user to log in and grant permissions.
    """
    browser_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(browser_path))


def configure_browser() -> None:
    """
    Configures the browser to be used during the OAuth2 flow for user authentication.

    This function registers Google Chrome as the default browser to handle the OAuth2
    process, allowing the user to log in and grant permissions. It detects the current
    operating system (Windows, macOS, or Linux) and sets the correct browser path.
    """
    current_os = platform.system()

    if current_os == "Windows":
        # Windows: Default Chrome installation path
        browser_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    elif current_os == "Darwin":
        # macOS: Default Chrome installation path for macOS
        browser_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif current_os == "Linux":
        # Linux: Default Chrome executable (assuming Chrome is installed in the PATH)
        browser_path = "/usr/bin/google-chrome"
    else:
        print(f"Unsupported operating system: {current_os}")
        return

    if os.path.exists(browser_path):
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser(browser_path))
    else:
        print(f"Chrome browser not found at: {browser_path}. Falling back to default browser.")


def request_credentials(scopes: list[str]) -> Credentials:
    """
    Requests OAuth2 credentials from the user by launching the browser and running 
    a local server to handle the callback.

    Args:
        scopes (list[str]): List of scopes required for the Google API service.

    Returns:
        Credentials: OAuth2 credentials object.

    If the client secrets file is present, it runs the installed OAuth flow
    using the Google Auth library, saves the credentials in a token file, and 
    returns the generated credentials.
    """
    creds: Credentials | None = None
    if os.path.exists(CLIENT_SECRETS_FILE):
        # Start OAuth2 flow
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, scopes)
        configure_browser()
        creds = flow.run_local_server(port=0)
        print()
        # Save credentials to a token file for later use
        with open(TOKEN_FILE, "w", encoding="utf-8") as token:
            token.write(creds.to_json())
        return Credentials.from_authorized_user_file(TOKEN_FILE, scopes)

    print("Credentials file not present.")
    sys.exit(1)  # Exit if the credentials file does not exist


def get_credentials(service_name):
    """
    Retrieves OAuth2 credentials from a token file if it exists, or requests new 
    credentials if not present.

    Args:
        service_name (str): The name of the Google API service (e.g., 'drive').

    Returns:
        Credentials: OAuth2 credentials object.

    The function checks if the token file exists and reads from it. If the credentials 
    are expired but have a refresh token, it will refresh them automatically.
    """
    scopes: list[str] = API_SERVICES[service_name]["scopes"]
    if os.path.exists(TOKEN_FILE):
        # Load credentials from the token file
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, scopes)
        # Refresh the token if it has expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

    # Request new credentials if token file is not found
    return request_credentials(scopes)


def create_service(api_service_name: str):
    """
    Creates a service object for interacting with a Google API.

    Args:
        api_service_name (str): The name of the API service to create (e.g., 'drive').

    Returns:
        googleapiclient.discovery.Resource: A service object for the Google API.

    The function retrieves the appropriate credentials and uses them to build a 
    service object that can be used to interact with Google APIs (such as Google Drive).
    """
    # Get service configuration and credentials
    api_service: str = API_SERVICES.get(api_service_name.lower(), None)
    service_name: str = api_service["service_name"]
    credentials: Credentials = get_credentials(service_name)

    # Build and return the service object
    service = build(service_name, API_VERSION, credentials=credentials)
    return service
