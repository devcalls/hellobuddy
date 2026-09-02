import os
import json
from pathlib import Path
from typing import List, Any


def write_to_file(content: str, file_path: str, file_name: str = None):
    """Writes the provided content to a file at the specified path."""
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    full_file_path = file_path if not file_name else os.path.join(directory, file_name)

    with open(full_file_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[File System] Successfully wrote content to: {full_file_path}")


def write_json_list_to_file(
    data_list: List[Any], file_path: str, file_name: str = None
):
    """Writes the provided content to a file at the specified path."""

    if os.path.isdir(file_path):
        actual_name = file_name if file_name else "job_history.json"
        full_file_path = os.path.join(file_path, actual_name)
    else:
        full_file_path = (
            file_path if not file_name else os.path.join(file_path, file_name)
        )

    # 2. Extract the directory portion of the path
    target_dir = os.path.dirname(full_file_path)

    # 3. Create the directories if they don't exist yet
    # exist_ok=True prevents a race condition crash if the folder is created simultaneously by another thread
    if target_dir and not os.path.exists(target_dir):
        print(f"[File System] Creating missing directory structure: {target_dir}")
        os.makedirs(target_dir, exist_ok=True)

    serializable_list = []
    for item in data_list:
        # Check if the item is a Pydantic model object
        if hasattr(item, "model_dump") and callable(item.model_dump):
            serializable_list.append(item.model_dump(mode="json"))
        else:
            serializable_list.append(item)

    with open(full_file_path, "w", encoding="utf-8") as f:
        json.dump(serializable_list, f, indent=4, ensure_ascii=False)

    print(f"[File System] Successfully wrote content to: {full_file_path}")


def read_json_from_file(file_path: str) -> list:
    """Reads a JSON file and returns its content as a list."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found at: {file_path}")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        raise ValueError(f"Failed to read or parse JSON file at {file_path}: {e}")

    print(f"[File System] Successfully read JSON content from: {file_path}")
    return data


def get_absolute_path(raw_path: str) -> Path:

    # Convert the string into a Cross-Platform Path object
    target_path = Path(raw_path)

    # Check if the user specified a relative or absolute anchor string
    if not target_path.is_absolute():
        # If relative (like './reports/'), anchor it dynamically to your project folder root!
        raise ValueError(
            f"The path '{raw_path}' is relative. Please provide an absolute path in the configuration file."
        )
    else:
        # If already absolute (like '/var/tmp' or 'C:\Users\...'), just normalize the slash symbols
        absolute_target = target_path.resolve()

    return absolute_target


def create_folder(file_path: str, folder_name: str):
    base_path = Path(file_path)
    new_dir = base_path.joinpath(folder_name)

    # Create the directory
    new_dir.mkdir(parents=True, exist_ok=True)
