import os
import sys
import argparse

def check_folder_exists(folder_path):
    """
    Checks if a folder exists at the given path.

    :param folder_path: Path to the folder to check.
    """
    if not os.path.isdir(folder_path):
        print(f"Error: The folder at path '{folder_path}' does not exist.")
        sys.exit(1)  # Exit with a non-zero status code to indicate an error.
    # print(f"Folder '{folder_path}' exists.")

def calculate_filtered_size(path, allowed_extensions):
    """
    Recursively calculates the size of files in a directory, filtering by allowed extensions.
    """
    total_size = 0
    for root, _, files in os.walk(path):
        for file in files:
            if file.lower().endswith(allowed_extensions):
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
    return total_size

def human_readable_size(size_in_bytes, use_decimal=True):
    """
    Converts a size in bytes to a human-readable format (e.g., MB, GB) with two decimal places.
    Allows switching between decimal (SI) and binary (IEC) units.
    """
    if use_decimal:
        units = ['bytes', 'KB', 'MB', 'GB', 'TB']
        divisor = 1000  # SI uses 1,000 as the divisor
    else:
        units = ['bytes', 'KiB', 'MiB', 'GiB', 'TiB']
        divisor = 1024  # IEC uses 1,024 as the divisor

    for unit in units:
        if size_in_bytes < divisor:
            return f"{size_in_bytes:.2f} {unit}"
        size_in_bytes /= divisor

    return f"{size_in_bytes:.2f} PB"  # If we go beyond TB

def count_files(path, allowed_extensions):
    file_count = 0
    for root, _, files in os.walk(path):
        for file in files:
            if file.lower().endswith(allowed_extensions):
                file_count += 1
    return file_count

def find_matching_backup_folder(source_folder_name, backup_root):
    """
    Searches for a matching folder in the backup root directory.
    """
    for root, dirs, _ in os.walk(backup_root):
        if source_folder_name in dirs:
            return os.path.join(root, source_folder_name)
    return None

def get_source_directories(source_root):
    """
    Returns a list of all subdirectories in the source root.
    """
    try:
        return [
            os.path.join(source_root, folder)
            for folder in os.listdir(source_root)
            if os.path.isdir(os.path.join(source_root, folder))
        ]
    except Exception as e:
        print(f"Error reading source root directory '{source_root}': {e}")
        return []

def compare_folder_sizes_with_filter(source_root, backup_root, allowed_extensions):
    """
    Compares the sizes of folders in the source root directory with their counterparts
    in the backup root directory, filtering files by allowed extensions.
    """
    mismatches = []
    source_total_size = 0
    backup_total_size = 0
    source_total_files = 0
    backup_total_files = 0

    source_directories = sorted(get_source_directories(source_root))

    for source_path in source_directories:
        folder = os.path.basename(source_path)
        backup_path = find_matching_backup_folder(folder, backup_root)

        if backup_path:
            source_size = calculate_filtered_size(source_path, allowed_extensions)
            backup_size = calculate_filtered_size(backup_path, allowed_extensions)
            source_file_count = count_files(source_path, allowed_extensions)
            backup_file_count = count_files(backup_path, allowed_extensions)

            source_total_size += source_size
            backup_total_size += backup_size
            source_total_files += source_file_count
            backup_total_files += backup_file_count

            if source_size != backup_size:
                mismatches.append((folder, source_size, backup_size))
                print(
                    f"Mismatch in '{folder}': "
                    f"Source={source_size} bytes ({human_readable_size(source_size)}), "
                    f"Backup={backup_size} bytes ({human_readable_size(backup_size)})"
                )
            else:
                print(
                    f"Matched '{folder}': "
                    f"Size={source_size} bytes ({human_readable_size(source_size)})"
                    f" | File Count={backup_file_count}"
                )
        else:
            mismatches.append((folder, None, None))
            print(f"folder ({folder}) is not in any of the parent target directory {backup_root}")

    print("\nGrand Total:")
    print(f"Source: {source_total_size} bytes ({human_readable_size(source_total_size)})")
    print(f"Backup: {backup_total_size} bytes ({human_readable_size(backup_total_size)})")
    print(f"Backup File Count: {backup_total_files}")
    if mismatches:
        print(f"Local File Count: {source_total_files} (check count in camera)")

    return mismatches

def parse_arguments():
    """
    Parses command-line arguments for source, backup, and allowed file extensions.
    """
    parser = argparse.ArgumentParser(description="Compare folder sizes based on file extensions.")
    parser.add_argument(
        "source_root",
        help="Path to the source root directory.",
    )
    parser.add_argument(
        "backup_root",
        help="Path to the backup root directory.",
    )
    parser.add_argument(
        "--camera",
        choices=["default", "sony", "olympus"],
        default="default",
        help="Specify the camera type to adjust allowed extensions. Default is '.dng'.",
    )
    return parser.parse_args()

def get_allowed_extensions(camera_type):
    """
    Returns the allowed extensions based on the specified camera type.
    """
    if camera_type == "sony":
        return (".arw", ".mov")
    if camera_type == "olympus":
        return (".orf", ".mov")
    return (".dng",".jpg")

if __name__ == "__main__":
    args = parse_arguments()
    allowed_extensions = get_allowed_extensions(args.camera)

    # since I often don't have the backup drive mounted, let's check fbefore doing the main comparison
    check_folder_exists(args.backup_root)
    check_folder_exists(args.source_root)

    mismatches = compare_folder_sizes_with_filter(args.source_root, args.backup_root, allowed_extensions)

    if mismatches:
        print("\nSummary of mismatches:")
        for folder, source_size, backup_size in mismatches:
            if backup_size is None:
                print(f"- folder ({folder}) is not in any of the parent target directory {args.backup_root}")
            else:
                print(
                    f"- {folder}: Source Size={source_size} bytes ({human_readable_size(source_size)}), "
                    f"Backup Size={backup_size} bytes ({human_readable_size(backup_size)})"
                )
    else:
        print("\nAll folders match!")
