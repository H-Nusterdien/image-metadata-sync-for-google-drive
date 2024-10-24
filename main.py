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

import os
import exiftool
import google_api

# Constants for local folder path and Google Drive folder ID
LOCAL_FOLDER_PATH: str = "./images"
GOOGLE_DRIVE_FOLDER_ID: str = ""


def get_list_of_image_files(dir_path: str) -> list[str]:
    """
    Get a list of image files (jpg, png, jpeg) from a specified directory.

    Args:
        dir_path (str): Path to the directory containing images.

    Returns:
        list[str]: List of image file names found in the directory.
    """
    list_of_image_files: list[str] = []
    for image_file in os.listdir(dir_path):
        image_file_with_lower_case: str = image_file.lower()
        # Check if the file is an image based on its extension
        if image_file_with_lower_case.endswith(('.jpg', '.png', '.jpeg')):
            list_of_image_files.append(image_file)
    return list_of_image_files


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


def search_image_in_drive(service, folder_id: str, image_name: str) -> list[dict[str, str]]:
    """
    Search for an image in a specific Google Drive folder by its name.

    Args:
        service: Google Drive API service instance.
        folder_id (str): Google Drive folder ID to search within.
        image_name (str): Name of the image to search for.

    Returns:
        list: List of files found in Google Drive with matching name.
    """
    # Build query to search for image in specified folder
    query: str = f"'{folder_id}' in parents and name = '{image_name}'"
    fields: str = "files(id, name)"
    results = service.files().list(q=query, fields=fields).execute()
    files = results.get('files', [])
    return files


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


def bulk_update_image_descriptions(drive_service, local_folder: str) -> None:
    """
    Perform a bulk update of image descriptions in Google Drive based on local image metadata.

    Args:
        local_folder (str): Path to the folder containing local images.
        drive_service: Google Drive API service instance.
    """
    image_files: list[str] = get_list_of_image_files(LOCAL_FOLDER_PATH)
    print_prefix: str = "\t -->"

    if not image_files:
        # No image files found in the folder
        print(f"{print_prefix} Failed: No image files found in the folder.")
        return

    # Create a batch request object for Google Drive API
    batch = drive_service.new_batch_http_request(callback=batch_callback)

    for image_file in image_files:
        print(f"In Progress: {image_file}")

        file_path: str = os.path.join(local_folder, image_file)

        # Extract the metadata (tags) from the local image file
        image_tags: list[str] = extract_tags_property(file_path)

        if image_tags:
            print(f"{print_prefix} Success: Extracted tags")
            new_description: str = create_description_from_tags(image_tags)

            # Search for the corresponding file in Google Drive
            drive_files: list[dict[str, str]] = search_image_in_drive(
                drive_service,
                GOOGLE_DRIVE_FOLDER_ID,
                image_file
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
    bulk_update_image_descriptions(google_drive_service, LOCAL_FOLDER_PATH)

    print(print_script_end)


# Entry point for the script execution
if __name__ == "__main__":
    main()
