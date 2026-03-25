"""Compare student output CSVs against golden reference files."""

from __future__ import annotations

import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_DIR = Path(__file__).resolve().parent / "expected"
OUTPUT_DIR = ROOT / "output" / "by_neighborhood"

NEIGHBORHOODS = [
    "downtown",
    "green_valley",
    "hillcrest",
    "lakeside",
    "maple_heights",
    "oakwood",
    "old_town",
    "riverside",
    "suburban_park",
    "university_district",
]


def read_csv(path: Path) -> list[dict]:
    """Read a CSV file robustly: strips BOM, normalises line endings, returns rows as dicts."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):  # strip UTF-8 BOM
        raw = raw[3:]
    text = raw.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)


# Function for bool case comparison because this should be caught
def rows_equal(expected_row, actual_row):
    """Compare two rows with boolean case insensitivity"""
    if len(expected_row) != len(actual_row):
        return False

    for e, a in zip(expected_row, actual_row):
        # Check if both are boolean strings (case-insensitive)
        if isinstance(e, str) and isinstance(a, str):
            if e.lower() in ("true", "false") and a.lower() in ("true", "false"):
                if e.lower() != a.lower():
                    return False
                continue
        # Regular comparison for non-boolean values
        if e != a:
            return False
    return True


failures: list[str] = []

for hood in NEIGHBORHOODS:
    expected_path = EXPECTED_DIR / f"{hood}.csv"
    actual_path = OUTPUT_DIR / f"{hood}.csv"

    if not actual_path.exists():
        failures.append(f"MISSING  {actual_path.relative_to(ROOT)}")
        continue

    expected_rows = read_csv(expected_path)
    actual_rows = read_csv(actual_path)

    # Compare row counts first for a clear error message
    if len(expected_rows) != len(actual_rows):
        failures.append(
            f"ROW COUNT MISMATCH  {hood}.csv: "
            f"expected {len(expected_rows)}, got {len(actual_rows)}"
        )
        continue

    # Compare row by row (files are already sorted by house_id)
    mismatches = [
        i
        for i, (e, a) in enumerate(zip(expected_rows, actual_rows))
        if not rows_equal(e, a)
    ]
    if mismatches:
        idx = mismatches[0]
        failures.append(
            f"CONTENT MISMATCH  {hood}.csv row {idx + 2}: "  # +2 for header + 1-based
            f"expected {expected_rows[idx]}, got {actual_rows[idx]}"
        )

if failures:
    print("FAILED")
    for msg in failures:
        print(f"  {msg}")
    sys.exit(1)

print(f"OK — all {len(NEIGHBORHOODS)} CSV files match the reference output.")
