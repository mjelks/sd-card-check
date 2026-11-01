import os
import re
import sys
import argparse
from collections import Counter
from datetime import datetime

from compare_files import get_allowed_extensions, check_folder_exists


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date '{value}', expected YYYY-MM-DD.")


# Renamed files look like "09.23.2026_09.26.54-0001-leica m10p.dng"
FILENAME_DATE = re.compile(r"^(\d{2})\.(\d{2})\.(\d{4})_")


def date_from_filename(name):
    """Returns the date encoded at the start of the filename, or None."""
    match = FILENAME_DATE.match(name)
    if not match:
        return None
    month, day, year = match.groups()
    try:
        return datetime(int(year), int(month), int(day))
    except ValueError:
        return None


def count_files_in_range(path, allowed_extensions, from_date, to_date):
    """
    Recursively counts files matching the extensions whose filename date falls
    within from_date..to_date (inclusive). Returns (total, per-day Counter, per-extension Counter, unparsed paths).
    """
    per_day = Counter()
    per_ext = Counter()
    unparsed = []

    for root, _, files in os.walk(path):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext not in allowed_extensions:
                continue
            file_date = date_from_filename(file)
            if file_date is None:
                unparsed.append(os.path.join(root, file))
            elif from_date <= file_date <= to_date:
                per_day[file_date.strftime("%Y-%m-%d")] += 1
                per_ext[ext] += 1

    return sum(per_day.values()), per_day, per_ext, unparsed


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Count files in a folder between two dates (by the MM.DD.YYYY_ date in the filename), filtered by camera type."
    )
    parser.add_argument("folder", help="Path to the folder to check.")
    parser.add_argument("from_date", type=parse_date, help="Start date, YYYY-MM-DD (inclusive).")
    parser.add_argument("to_date", type=parse_date, help="End date, YYYY-MM-DD (inclusive).")
    parser.add_argument(
        "--camera",
        choices=["default", "sony", "olympus"],
        default="default",
        help="Camera type to adjust allowed extensions. Default is '.dng' and '.jpg'.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    if args.from_date > args.to_date:
        print("Error: FROM date is after TO date.")
        sys.exit(1)

    check_folder_exists(args.folder)
    allowed_extensions = get_allowed_extensions(args.camera)

    total, per_day, per_ext, unparsed = count_files_in_range(
        args.folder, allowed_extensions, args.from_date, args.to_date
    )

    print(
        f"Folder: {args.folder}\n"
        f"Range:  {args.from_date:%Y-%m-%d} to {args.to_date:%Y-%m-%d}\n"
        f"Camera: {args.camera} ({', '.join(allowed_extensions)})\n"
    )
    for day in sorted(per_day):
        print(f"  {day}: {per_day[day]}")
    print("\nBy extension:")
    for ext in allowed_extensions:
        print(f"  {ext}: {per_ext[ext]}")
    print(f"\nTotal files: {total}")
    if unparsed:
        print(f"\nSkipped {len(unparsed)} file(s) with no date in the filename (not renamed yet?):")
        for path in unparsed[:10]:
            print(f"  {path}")
        if len(unparsed) > 10:
            print(f"  ... and {len(unparsed) - 10} more")
