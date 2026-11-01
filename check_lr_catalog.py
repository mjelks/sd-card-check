import os
import sqlite3
import re
import subprocess
import sys
from collections import Counter
from urllib.parse import quote

SUPPORTED_EXTENSIONS = (".dng", ".arw", ".cr2", ".nef", ".orf")

def get_lightroom_capture_counts(catalog_path):
    """Return a Counter of capture time (to the second) -> number of images in the catalog.

    Lightroom Classic stores no content checksums, and converted DNGs are renamed,
    so capture time is the only key that survives the ORF -> DNG conversion.
    """
    # Read-only so a bad path can't create an empty database
    conn = sqlite3.connect(f"file:{quote(catalog_path)}?mode=ro", uri=True)
    try:
        rows = conn.execute("SELECT captureTime FROM Adobe_images WHERE captureTime IS NOT NULL")
        return Counter(row[0][:19] for row in rows)
    finally:
        conn.close()

def get_card_capture_times(sd_card_path):
    """Return [(file_path, capture time)] for RAW files on the card, via exiftool."""
    args = ["exiftool", "-r", "-q", "-T", "-d", "%Y-%m-%dT%H:%M:%S",
            "-FilePath", "-DateTimeOriginal"]
    for ext in SUPPORTED_EXTENSIONS:
        args += ["-ext", ext.lstrip(".")]
    try:
        out = subprocess.run(args + [sd_card_path], capture_output=True, text=True, check=True).stdout
    except FileNotFoundError:
        sys.exit("exiftool is required (brew install exiftool)")
    files = []
    for line in out.splitlines():
        path, _, taken = line.partition("\t")
        files.append((path, taken if taken and taken != "-" else None))
    return sorted(files)

def find_missing_files(sd_card_path, catalog_counts):
    """Return card files with no matching capture time in the catalog.

    Files sharing a timestamp (bursts) are matched by count, so the catalog must hold
    at least as many images at that second as the card does.
    """
    missing = []
    seen = Counter()
    for path, taken in get_card_capture_times(sd_card_path):
        if taken is None:
            missing.append(path)
            continue
        seen[taken] += 1
        if catalog_counts[taken] < seen[taken]:
            missing.append(path)
    return missing

def clean_path(raw):
    """Handle quotes and shell-style escapes from dragged/pasted paths."""
    path = raw.strip().strip("'\"")
    path = re.sub(r"\\(.)", r"\1", path)
    return os.path.expanduser(path)

def main():
    sd_card_path = clean_path(input("Enter the SD card path: "))
    catalog_path = clean_path(input("Enter the Lightroom catalog path: "))

    if not os.path.isdir(sd_card_path):
        sys.exit(f"SD card path not found: {sd_card_path!r}")
    if not os.path.isfile(catalog_path):
        sys.exit(f"Catalog not found: {catalog_path!r} (check for stray spaces)")

    print("Reading Lightroom catalog...")
    catalog_counts = get_lightroom_capture_counts(catalog_path)
    
    print("Checking files on SD card...")
    missing_files = find_missing_files(sd_card_path, catalog_counts)
    
    if missing_files:
        print("The following RAW files are not in the Lightroom catalog:")
        for file in missing_files:
            print(file)
    else:
        print("All RAW files on the SD card exist in the Lightroom catalog.")

if __name__ == "__main__":
    main()
