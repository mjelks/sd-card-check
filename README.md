# sd-card-check

Small Python utilities for checking photos before you wipe an SD card. They answer two questions:

1. **Did everything I shot make it to my import and backup folders?** Count files by date range (`count_files_by_date.py`) and compare the totals.
2. **Is everything on the card already in my Lightroom catalog?** (`check_lr_catalog.py`)

A third script, `compare_files.py`, is the safest pre-format check: compare every file downloaded from the card against the backup and audit anything missing. See [`compare_files.py`](#compare_filespy-compare-the-cards-files-against-the-backup).

## Overview

The scripts are a safety check for the author's import workflow. Nothing is wiped from the card until the checks pass.

1. **Import** the files from the SD card into `~/Pictures`.
2. **Rename** them with an `exiftool` script, which puts each file in a folder named for its capture date and prefixes the filename with the date and time, a sequence number and a camera tag:

   ```
   10.30.2026/10.30.2026_14.00.49-0001-epl5.orf
   ```

   The `MM.DD.YYYY_` prefix is what `count_files_by_date.py` reads.
3. **Move** the renamed date folders into the per-camera import folder under `~/Pictures` (e.g. `~/Pictures/imports-leica-m10p`).
4. **Verify** with the scripts below, then wipe the card.

The folders to check are passed on the command line, typically through a shell alias (see [Bash profile installation](#bash-profile-installation)). The scripts rely on the naming and layout above. See the [TODO](#todo) for making them configurable.

- **`count_files_by_date.py`** is the main check. Because every file is renamed with a leading `MM.DD.YYYY_` date, it can count how many photos fall between two dates in any folder, with a per-day and per-extension breakdown. Run it on the import folder and again on the backup location (wherever your "Backups" directory is) with the same date range. If the totals match each other, and match the count your camera reports, nothing was lost. Any file without a date prefix is listed as not yet renamed. It only looks at filenames, not folder names, so it doesn't matter how the backup is organized.

- **`check_lr_catalog.py`** is the Lightroom check. It reads the capture time (EXIF `DateTimeOriginal`) of every raw file on the card and compares it against the capture times in your Lightroom catalog. It lists any card files Lightroom doesn't know about, so you can catch photos that were never imported. Lightroom stores no content checksums and the renamed, converted DNGs no longer share names with the card's files, so capture time is the key that survives both.

Python 3.8+ and the standard library only. `check_lr_catalog.py` also needs `exiftool` (`brew install exiftool`), which the renaming step already uses.

## Scripts

### `count_files_by_date.py`: count photos in a date range

Counts files whose **filename** starts with a `MM.DD.YYYY_` date, such as `09.23.2026_09.26.54-0001-leica m10p.dng`. This is the format produced by the renaming step in the workflow above. Files without that prefix are skipped and listed at the end, so you can spot anything not yet renamed.

```
python3 count_files_by_date.py FOLDER FROM_DATE TO_DATE [--camera {default,sony,olympus}]
```

Dates are `YYYY-MM-DD` and the range is inclusive. The folder is searched recursively.

| `--camera` | Extensions counted |
|------------|--------------------|
| `default`  | `.dng`, `.jpg`     |
| `sony`     | `.arw`, `.mov`     |
| `olympus`  | `.orf`, `.mov`     |

Example: count the same range in the import folder and in the backup, then compare the totals.

```
$ python3 count_files_by_date.py ~/Pictures/imports-leica-m10p 2026-09-20 2026-09-25
Folder: /Users/me/Pictures/imports-leica-m10p
Range:  2026-09-20 to 2026-09-25
Camera: default (.dng, .jpg)

  2026-09-22: 87
  2026-09-23: 140

By extension:
  .dng: 227
  .jpg: 0

Total files: 227

$ python3 count_files_by_date.py /Volumes/Backup/Photos 2026-09-20 2026-09-25
...
Total files: 227
```

### `check_lr_catalog.py`: find files missing from Lightroom

Prompts for an SD card path and a Lightroom catalog (`.lrcat`) path. It reads the capture time of every raw file on the card (`.dng .arw .cr2 .nef .orf`) with `exiftool` and lists any whose capture time isn't in the catalog. Files sharing a timestamp (bursts) are matched by count.

```
python3 check_lr_catalog.py
Enter the SD card path: /Volumes/SD
Enter the Lightroom catalog path: ~/Pictures/Lightroom/Catalog.lrcat
```

The catalog is only read, and Lightroom can be open or closed. A file with no capture time is always reported. Two cameras shooting in the same second can mask a missing file, and photos deleted from the catalog show up as missing.

**Checking the results:** after `The following RAW files are not in the Lightroom catalog:`, the script prints one path per line. To eyeball them, paste the list into a file and open them all in Preview (the embedded JPEG previews are shown for ORFs):

```bash
# paste the listed paths into missing.txt, then:
tr '\n' '\0' < missing.txt | xargs -0 open -a Preview
```

Or open a handful by hand:

```bash
open -a Preview "/Volumes/LEICA M/DCIM/102OLYMP/P7140110.ORF" "/Volumes/LEICA M/DCIM/102OLYMP/P7140111.ORF"
```

### `compare_files.py`: compare the card's files against the backup

The safest check before formatting an SD card, especially if you forgot to verify earlier:

1. Download **all** raw files from the card.
2. Place them in the source comparison folder.
3. Run this script and look for mismatches or missing files.
4. Audit anything reported missing (for example, test shots you chose not to back up) using the Preview command it prints.

For each top-level folder in the source, it finds a folder with the same name anywhere under the backup root. It then compares the total size and file count of the matching files, and reports folders that differ or are missing from the backup.

```
python3 compare_files.py SOURCE_ROOT BACKUP_ROOT [--camera {default,sony,olympus}]
```

If anything mismatches, the summary lists each mismatched folder, followed by a ready-to-paste command that opens every missing file in Preview. A file counts as missing if the backup has no file with the same name, or has one with a different size (which also catches partial copies). Every file in a folder that isn't in the backup at all is included.

```
Summary of mismatches:
- 10.31.2026: Source Size=5164466058 bytes (5.16 GB), Backup Size=4935356429 bytes (4.94 GB)
- folder (11.01.2026) is not in any of the parent target directory /Volumes/Backup/Photos

To review missing files in Preview:
open -a Preview /path/to/file1.dng /path/to/file2.dng
```

It only works when the source and backup have identically named folders. It also exits with an error if either folder doesn't exist, which is handy when the backup drive isn't mounted.

`count_files_by_date.py` imports two helpers from this file (`get_allowed_extensions` and `check_folder_exists`). See the [TODO](#todo).

## Bash profile installation

Clone the repo somewhere permanent:

```bash
git clone https://github.com/<your-username>/sd-card-check.git ~/Sites/projects/sd-card-check
```

Add this to `~/.zshrc` (macOS default) or `~/.bash_profile` / `~/.bashrc`:

```bash
# sd-card-check
export SD_CARD_CHECK="$HOME/Sites/projects/sd-card-check"

# sdcount FOLDER FROM TO [--camera sony|olympus]
alias sdcount='python3 "$SD_CARD_CHECK/count_files_by_date.py"'

# sdlr  (interactive)
alias sdlr='python3 "$SD_CARD_CHECK/check_lr_catalog.py"'
```

Reload your shell:

```bash
source ~/.zshrc    # or: source ~/.bash_profile
```

Now use them from anywhere:

```bash
# import folder, then backup, same range: totals should match
sdcount ~/Pictures/imports-leica-m10p 2026-09-20 2026-09-25
sdcount /Volumes/Backup/Photos 2026-09-20 2026-09-25
sdlr
```

### Optional: shortcuts with your paths baked in

If you always use the same import and backup locations, bake the folder into an alias so you only type the dates:

```bash
# Count files in the backup location; pass FROM and TO when you run it
alias check_backup_count='python3 "$SD_CARD_CHECK/count_files_by_date.py" /Volumes/Backup/Photos'
```

```bash
check_backup_count 2026-09-20 2026-09-25
```

The folder is the first argument, so the alias supplies it and the dates (and any `--camera` flag) follow. An equivalent alias for the import folder works the same way:

```bash
alias check_import_count='python3 "$SD_CARD_CHECK/count_files_by_date.py" ~/Pictures/imports-leica-m10p'
```

Or, for a rolling "last N days" window, use functions:

```bash
# Photos in the last N days (default 7) in the import folder; macOS `date -v`
sdrecent() {
  local days="${1:-7}"
  python3 "$SD_CARD_CHECK/count_files_by_date.py" \
    "$HOME/Pictures/imports-leica-m10p" "$(date -v-"${days}"d +%Y-%m-%d)" "$(date +%Y-%m-%d)"
}

# Same range in the backup location
sdrecent_backup() {
  local days="${1:-7}"
  python3 "$SD_CARD_CHECK/count_files_by_date.py" \
    "/Volumes/Backup/Photos" "$(date -v-"${days}"d +%Y-%m-%d)" "$(date +%Y-%m-%d)"
}
```

For another camera, point the function at the matching import folder and pass `--camera`, e.g. `~/Pictures/imports-olympus --camera olympus`.

### Compare alias

For the folder comparison:

```bash
alias sdcompare='python3 "$SD_CARD_CHECK/compare_files.py"'   # sdcompare SOURCE BACKUP [--camera ...]
```

## Notes

- `count_files_by_date.py` imports helpers from `compare_files.py`, so keep them in the same directory.
- Extension matching is case-insensitive.

## TODO

Future enhancements. The scripts currently assume a specific naming convention and folder layout.

- [ ] **Move shared helpers.** Move `get_allowed_extensions` and `check_folder_exists` into a shared module (e.g. `common.py`) that both `count_files_by_date.py` and `compare_files.py` import.
- [ ] **Compare two folders in one run.** Let `count_files_by_date.py` take multiple folders (import and backup) and report the totals side by side, flagging any difference, so the two-command check becomes one.
- [ ] **Configurable filename date prefix** in `count_files_by_date.py`. The `MM.DD.YYYY_` format is hardcoded in the `FILENAME_DATE` regex. Add an option (e.g. `--date-format "%Y-%m-%d"` or `--prefix-regex`) so other renaming schemes work.
- [ ] **Configurable file extensions.** The per-camera lists in `get_allowed_extensions()` and `SUPPORTED_EXTENSIONS` in `check_lr_catalog.py` are hardcoded. Add an `--extensions` flag or a config file, and add more camera presets.
- [ ] **Command-line arguments for `check_lr_catalog.py`.** It currently prompts interactively for paths, unlike `count_files_by_date.py`.
- [ ] **Shared config file** (e.g. `config.toml`) for the settings above, so the bash aliases stay short.
