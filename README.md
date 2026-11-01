# sd-card-check

Small Python utilities for checking photos before you wipe an SD card. They answer three questions:

1. **Did everything on the card make it to my backup drive?** (`compare_files.py`)
2. **How many photos did I shoot between two dates?** (`count_files_by_date.py`)
3. **Is everything on the card already in my Lightroom catalog?** (`check_lr_catalog.py`)

Python 3.8+ and the standard library only, with nothing to install.

## Scripts

### `compare_files.py`: compare card against backup

For each top-level folder in the source (e.g. `DCIM/100OLYMP`), it finds a folder with the same name anywhere under the backup root. It then compares the total size and file count of the matching files. Folders that match are reported as matched. Folders that differ in size, or are missing from the backup, are listed in a summary at the end.

```
python3 compare_files.py SOURCE_ROOT BACKUP_ROOT [--camera {default,sony,olympus}]
```

| `--camera` | Extensions compared |
|------------|---------------------|
| `default`  | `.dng`, `.jpg`      |
| `sony`     | `.arw`, `.mov`      |
| `olympus`  | `.orf`, `.mov`      |

It exits with an error if either folder doesn't exist, which is handy when the backup drive isn't mounted.

Example:

```
$ python3 compare_files.py /Volumes/SD/DCIM /Volumes/Backup/Photos --camera sony
Matched '100MSDCF': Size=8123456789 bytes (8.12 GB) | File Count=412
Mismatch in '101MSDCF': Source=1200000 bytes (1.20 MB), Backup=0 bytes (0.00 bytes)

Grand Total:
Source: 8124656789 bytes (8.12 GB)
Backup: 8123456789 bytes (8.12 GB)
Backup File Count: 412
Local File Count: 413 (check count in camera)

Summary of mismatches:
- 101MSDCF: Source Size=1200000 bytes (1.20 MB), Backup Size=0 bytes (0.00 bytes)
```

### `count_files_by_date.py`: count photos in a date range

Counts files whose **filename** starts with a `MM.DD.YYYY_` date, such as `09.23.2026_09.26.54-0001-leica m10p.dng`. This is the format produced by the renaming step in your import workflow. Files without that prefix are skipped and listed at the end, so you can spot anything not yet renamed.

```
python3 count_files_by_date.py FOLDER FROM_DATE TO_DATE [--camera {default,sony,olympus}]
```

Dates are `YYYY-MM-DD` and the range is inclusive.

Example:

```
$ python3 count_files_by_date.py ~/Pictures/2026 2026-09-20 2026-09-25
Folder: /Users/me/Pictures/2026
Range:  2026-09-20 to 2026-09-25
Camera: default (.dng, .jpg)

  2026-09-22: 87
  2026-09-23: 140

By extension:
  .dng: 227
  .jpg: 0

Total files: 227
```

### `check_lr_catalog.py`: find files missing from Lightroom

Prompts for an SD card path and a Lightroom catalog (`.lrcat`) path. It SHA-256 hashes every raw file on the card (`.dng .arw .cr2 .nef .orf`) and lists any whose checksum isn't recorded in the catalog.

```
python3 check_lr_catalog.py
Enter the SD card path: /Volumes/SD
Enter the Lightroom catalog path: ~/Pictures/Lightroom/Catalog.lrcat
```

The catalog is only read. Hashing a full card can take a while. Lightroom must have already computed hashes for the images, so `sha256` can be `NULL` for some photos; those are ignored.

## Bash profile installation

Clone the repo somewhere permanent:

```bash
git clone https://github.com/<your-username>/sd-card-check.git ~/Sites/projects/sd-card-check
```

Add this to `~/.zshrc` (macOS default) or `~/.bash_profile` / `~/.bashrc`:

```bash
# sd-card-check
export SD_CARD_CHECK="$HOME/Sites/projects/sd-card-check"

# sdcompare SOURCE BACKUP [--camera sony|olympus]
alias sdcompare='python3 "$SD_CARD_CHECK/compare_files.py"'

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
sdcompare /Volumes/SD/DCIM /Volumes/Backup/Photos --camera sony
sdcount ~/Pictures/2026 2026-09-20 2026-09-25
sdlr
```

### Optional: shortcuts with your paths baked in

If you always use the same card and backup locations, wrap them in functions:

```bash
# Check the mounted card against the backup drive
sdcheck() {
  python3 "$SD_CARD_CHECK/compare_files.py" \
    "/Volumes/SD_CARD/DCIM" "/Volumes/Backup/Photos" "$@"
}

# Photos shot in the last N days (default 7); macOS `date -v`
sdrecent() {
  local days="${1:-7}"
  python3 "$SD_CARD_CHECK/count_files_by_date.py" \
    "$HOME/Pictures" "$(date -v-"${days}"d +%Y-%m-%d)" "$(date +%Y-%m-%d)"
}
```

Extra arguments pass through, so `sdcheck --camera olympus` works.

## Notes

- `compare_files.py` and `count_files_by_date.py` share helpers, so keep them in the same directory (`count_files_by_date.py` imports from `compare_files.py`).
- Extension matching is case-insensitive.
- Folder matching in `compare_files.py` is by folder name, not full path, so the first match found under the backup root is used.
