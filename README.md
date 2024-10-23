# Google Drive Image Metadata Sync Script

This script allows you to bulk update the descriptions of image files in a Google Drive folder based on metadata extracted from local image files. It uses the Google Drive API to find corresponding images and batch update their descriptions based on the `Tags` metadata from the local images.

## Features

- Extracts metadata (`Tags`) from images using ExifTool.
- Searches for corresponding images in a Google Drive folder.
- Updates the description of Google Drive images in bulk using batch requests.
- Works with `.jpg`, `.jpeg`, and `.png` image files.

---

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Setting Up the Google API](#setting-up-the-google-api)
  - [Setting Up the Project](#setting-up-the-project)
- [Running the Script](#running-the-script)
  - [Windows Instructions](#windows-instructions)
  - [macOS Instructions](#macos-instructions)
  - [Linux Instructions](#linux-instructions)
- [Project Structure](#project-structure)

---

## Getting Started

### Prerequisites

Before running the script, ensure you have the following:

1. Python 3.x installed on your system.
2. `ExifTool` installed (to extract image metadata).
3. A Google Cloud Project set up for using Google APIs.
4. `client-secrets-file.json` from the Google Developer Console.

### Setting Up the Google API

1. **Create a Google Cloud Project**:
   - Go to the [Google Cloud Console](https://console.cloud.google.com/).
   - Create a new project.
   
2. **Enable the Google Drive API**:
   - In the "APIs & Services" > "Library" section, search for **Google Drive API** and enable it for your project.

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials".
   - Click on **Create Credentials** > **OAuth 2.0 Client IDs**.
   - Set the application type to **Desktop App** and download the `client-secrets-file.json`.

4. **Save the `client-secrets-file.json`**:
   - Place the downloaded file in the root of your project directory. This file will be used to authenticate the script with your Google Drive account.

### Setting Up the Project

1. **Clone the repository**:
   ```bash
   git clone https://github.com/H-Nusterdien/image-metadata-sync-for-google-drive.git
   cd image-metadata-sync-for-google-drive
   ```

2. **Create a virtual environment**: Create a virtual environment to keep dependencies isolated.
   - On Windows:
     ```bash
     python -m venv venv
     ```
   - On macOS/Linux:
     ```bash
     python3 -m venv venv
     ```

3. **Activate the virtual environment**:
   - On Windows:
     ```bash
     .\venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**: Install the required Python packages using the `requirements.txt` file:
   ```bash
   pip install -r requirements.txt
   ```

5. **Install ExifTool**: Download and install [ExifTool](https://exiftool.org/) based on your operating system
   - On Windows: Download the Windows Executable.
   - On macOS: Install using Homebrew.
     ```bash
     brew install exiftool
     ```
   - On Linux: Install using your package manager.
     ```bash
     sudo apt install libimage-exiftool-perl
     ```
---

## Running The Script

The script performs the following steps:

1. Reads all image files from a local directory (`./images` by default).
2. Extracts the `Tags` metadata from each image.
3. Searches for the corresponding image in a Google Drive folder.
4. Updates the description of the image in Google Drive based on the extracted tags.

### Windows Instructions

1. Make sure you have installed Python, ExifTool, and activated the virtual environment.
2. Run the script:
   ```bash
   python main.py
   ```
3. Follow the authentication flow in your browser to allow access to your Google Drive.
4. The script will process all the image files in the ./images folder and update their descriptions in Google Drive.

### macOS Instructions

1. Ensure Python, ExifTool, and the virtual environment are set up.
2. Run the script:
   ```bash
   python main.py
   ```
3. Authenticate with your Google account when prompted.
4. The script will process the images and update the Google Drive descriptions.

### Linux Instructions

1. Verify that Python, ExifTool, and the virtual environment are installed and activated.
2. Run the script:
   ```bash
   python main.py
   ```
3. Authenticate using the OAuth 2.0 flow in your browser.
4. The image metadata will be extracted, and the descriptions in Google Drive will be updated.

---

## Project Structure

```bash
image-metadata-sync-for-google-drive/
│
├── images/                     # Local folder containing image files
├── main.py                     # Main script for updating metadata in Google Drive
├── google_api.py               # Module for Google Drive API interactions
├── client-secrets-file.json    # OAuth 2.0 client secret (not included in repo)
├── token.json                  # Token file for authenticated Google API access
├── requirements.txt            # Python dependencies
├── venv/                       # Virtual environment directory
└── README.md                   # Project documentation
```

- `main.py`: The script that handles the bulk extraction of metadata and updates the corresponding images in Google Drive.
- `google_api.py`: Contains helper functions for creating the Google Drive API service, managing credentials, and making API calls.
- `client-secrets-file.json`: OAuth 2.0 credentials for accessing Google APIs (should not be committed to version control).
- `token.json`: File that stores access and refresh tokens for future authenticated requests.
- `requirements.txt`: Lists all the dependencies required to run the script.

---

## Notes

- `Google OAuth`: The first time you run the script, it will prompt you to authenticate and authorize access to your Google Drive. The token will be saved in token.json for future use.
- `API Limits`: Make sure to respect Google Drive API usage limits. If you have a large number of files, consider optimizing the batch size or implementing throttling to avoid hitting rate limits.
- `File Matching`: This script matches image files in your local folder with those in Google Drive by filename. Ensure the filenames are the same in both locations.
