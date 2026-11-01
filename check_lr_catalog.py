import os
import sqlite3
import hashlib

SUPPORTED_EXTENSIONS = (".dng", ".arw", ".cr2", ".nef", ".orf")

def calculate_checksum(file_path, algo="sha256"):
    """Calculate the checksum of a file."""
    hash_func = hashlib.new(algo)
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def get_lightroom_checksums(catalog_path):
    """Extract checksums from the Lightroom catalog database."""
    conn = sqlite3.connect(catalog_path)
    cursor = conn.cursor()
    query = """
        SELECT idx_files.absolutePath || idx_files.idx_filename AS full_path,
               Adobe_images.sha256
        FROM Adobe_images
        JOIN idx_files ON Adobe_images.rootFile = idx_files.id_local
        WHERE Adobe_images.sha256 IS NOT NULL;
    """
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()
    return {row[0]: row[1] for row in results}

def find_missing_files(sd_card_path, catalog_checksums):
    """Compare SD card files against Lightroom catalog checksums."""
    sd_card_checksums = {}
    for root, _, files in os.walk(sd_card_path):
        for file in files:
            if file.lower().endswith(SUPPORTED_EXTENSIONS):
                file_path = os.path.join(root, file)
                checksum = calculate_checksum(file_path)
                sd_card_checksums[file_path] = checksum
    
    missing_files = [f for f, c in sd_card_checksums.items() if c not in catalog_checksums.values()]
    return missing_files

def main():
    sd_card_path = input("Enter the SD card path: ").strip()
    catalog_path = input("Enter the Lightroom catalog path: ").strip()
    
    print("Reading Lightroom catalog...")
    catalog_checksums = get_lightroom_checksums(catalog_path)
    
    print("Checking files on SD card...")
    missing_files = find_missing_files(sd_card_path, catalog_checksums)
    
    if missing_files:
        print("The following DNG files are not in the Lightroom catalog:")
        for file in missing_files:
            print(file)
    else:
        print("All DNG files on the SD card exist in the Lightroom catalog.")

if __name__ == "__main__":
    main()
