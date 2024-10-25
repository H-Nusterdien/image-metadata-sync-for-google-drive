"""
main.py

This script synchronizes the metadata from local image files with their corresponding Google Drive files.
It extracts tags from the local image metadata using ExifTool and updates the description field of 
the matching images in a specified Google Drive folder.

Key Functions:
- `get_list_of_image_files`: Retrieves a list of image files (jpg, png, jpeg) from a local folder.
- `extract_tags_property`: Extracts the 'Tags' metadata from a local image file using ExifTool.
- `search_image_in_drive`: Searches for an image in a specific Google Drive folder by name.
- `update_description_of_drive_image`: Updates the description of an image file in Google Drive.
- `create_description_from_tags`: Creates a description string from a list of tags.
- `bulk_update_image_descriptions`: Performs batch processing to update image descriptions in Google Drive.

The script uses Google Drive's batch request feature to handle bulk updates efficiently. It is triggered 
from the `main` function, which initializes the Google Drive API service and processes all image files in 
the local folder.

Dependencies:
- exiftool
- google-api-python-client

Usage:
- Place images in the `./images` folder.
- Update the `GOOGLE_DRIVE_FOLDER_ID` constant with the appropriate Google Drive folder ID.
- Run the script to synchronize image descriptions between local and Google Drive.

"""

from pathlib import Path

import exiftool
import google_api


# Constants for local folder path and Google Drive folder ID
LOCAL_FOLDER_NAME: str = "images"
IMAGE_FILE_EXTENSIONS: tuple[str, ...] = (".jpg", ".jpeg", ".png")
GOOGLE_DRIVE_FOLDER_ID: str = ""


def get_list_of_image_paths(
        directory: str = LOCAL_FOLDER_NAME,
        extensions: tuple[str, ...] = IMAGE_FILE_EXTENSIONS
    ) -> list[str]:
    """
    Retrieves all image paths within a specified directory, including nested folders.

    Args:
    - directory (str): The root directory to search for images.
    - extensions (tuple): A tuple of file extensions to consider as images.

    Returns:
    - list[str]: A list of paths to all images found.
    """
    initial_dir = Path(directory)
    list_of_image_paths = [str(path) for path in initial_dir.rglob("*") if path.suffix.lower() in extensions]
    return list_of_image_paths


def extract_tags_property(image_path: str) -> list[str]:
    """
    Extract the 'Tags' property from the image's metadata using ExifTool.

    Args:
        image_path (str): Path to the image file.

    Returns:
        list[str]: Tags/keywords found in the image metadata.
    """
    with exiftool.ExifTool() as et:
        # Extract metadata from the image
        metadata = et.execute_json(image_path)
    # Get the 'IPTC:Keywords' field from the metadata
    tags: list[str] = metadata[0]["IPTC:Keywords"]
    return tags


def search_image_in_drive(
        service,
        image_path: str,
        root_folder_id: str = GOOGLE_DRIVE_FOLDER_ID
    ) -> list[dict[str, str]]:
    """
    Search for an image in Google Drive by mirroring the structure of the local path.

    Args:
        service: Google Drive API service instance.
        root_folder_id (str): Google Drive folder ID to start searching within.
        local_path (str): Local file path to mirror in Google Drive.

    Returns:
        list[dict[str, str]]: List of files found in Google Drive with matching name and structure.
    """
    # Split the local path into parts for each folder level
    path_parts = image_path.split('/')

    # Initialize the folder ID to start with
    current_folder_id = root_folder_id

    # Iterate through the path parts, assuming the last part is the file name
    for part in path_parts[:-1]:  # Exclude the last part (the file name)
        query = f"'{current_folder_id}' in parents and name = '{part}' and mimeType = 'application/vnd.google-apps.folder'"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if not folders:
            print(f"Folder '{part}' not found in the expected structure.")
            return []  # If any folder in the path isn't found, the structure doesn't match
        else:
            current_folder_id = folders[0]['id']  # Move to the next folder

    # Final search for the image file in the last matched folder
    image_name = path_parts[-1]
    image_query = (
        f"'{current_folder_id}' in parents and name contains '{image_name}' "
        f"and mimeType contains 'image/'"
    )
    image_results = service.files().list(q=image_query, fields="files(id, name)").execute()
    image_files = image_results.get('files', [])

    return image_files


def create_description_from_tags(tags: list[str]) -> str:
    """
    Create a description string from a list of tags.

    Args:
        tags (list[str]): List of tags extracted from image metadata.

    Returns:
        str: Formatted description string.
    """
    new_description: str = ""
    # Append each tag to the description string, separated by commas
    for tag in tags:
        new_description += f"{tag}, "
    # Remove trailing comma and space
    new_description = new_description[:-2]
    return new_description


def batch_callback(request_id, response, exception) -> None:
    """
    Callback function for batch requests to handle responses or exceptions.

    Args:
        request_id (str): ID of the batch request.
        response (dict): Response from Google Drive API for the request.
        exception (Exception): Exception encountered during the request, if any.
    """
    if exception:
        print(f"- Error in batch request {request_id}: {exception}")
    else:
        print(f"+ Successfully updated Google Drive image file | {response.get('name')}")


def bulk_update_image_descriptions(
        drive_service,
        local_folder_name: str = LOCAL_FOLDER_NAME
    ) -> None:
    """
    Perform a bulk update of image descriptions in Google Drive based on local image metadata.

    Args:
        local_folder_name (str): Path to the folder containing local images.
        drive_service: Google Drive API service instance.
    """
    list_of_image_paths: list[str] = get_list_of_image_paths()

    print_prefix: str = "\t -->"

    if not list_of_image_paths:
        # No image files found in the folder
        print(f"{print_prefix} Failed: No image files found in the folder.")
        return

    # Create a batch request object for Google Drive API
    batch = drive_service.new_batch_http_request(callback=batch_callback)

    for image_path in list_of_image_paths:
        print(f"In Progress: {image_path}")

        # Extract the metadata (tags) from the local image file
        image_tags: list[str] = extract_tags_property(image_path)
        # Remove the local folder name from the image path
        image_path = image_path.replace(f"{local_folder_name}/", "")

        if image_tags:
            print(f"{print_prefix} Success: Extracted tags")

            new_description: str = create_description_from_tags(image_tags)

            # Search for the corresponding file in Google Drive
            drive_files: list[dict[str, str]] = search_image_in_drive(
                drive_service,
                image_path
            )

            if drive_files:
                print(f"{print_prefix} Success: File found in Google Drive")

                for drive_file in drive_files:
                    file_id: str = drive_file['id']
                    # Prepare the update request to modify the description
                    request = drive_service.files().update(
                        fileId=file_id,
                        body={"description": new_description}
                    )
                    # Add the request to the batch
                    batch.add(request)
                    print(f"{print_prefix} Success: File added to batch processing")
            else:
                print(f"{print_prefix} Failed: No matching file found in Google Drive")
        else:
            print(f"{print_prefix} Failed: No tags found")

        print()

    print_batch_processing: str = "-"*100 + \
        "\n\t\t\t\tUpdate Description of Google Drive Images\n" + \
        "-"*100 + "\n"
    print(print_batch_processing)

    # Execute the batch request to update all files
    batch.execute()


def main() -> None:
    """
    Main function that initializes the Google Drive service and triggers the bulk update process.
    """
    print_script_start: str = "\n" + "="*100 + \
        "\n\t\t\t\tImage Metadata Sync for Google Drive\n" + \
        "="*100 + "\n"
    print_script_end: str = "\n" + "="*100 + \
        "\n\t\t\t\t\tEnd of Script\n" + \
        "="*100 + "\n"

    print(print_script_start)

    # Initialize the Google Drive API service
    google_drive_service = google_api.create_service("drive")
    # Perform bulk update of image descriptions
    bulk_update_image_descriptions(google_drive_service)

    print(print_script_end)


# Entry point for the script execution
if __name__ == "__main__":
    main()
