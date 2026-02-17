"""
scripts/export_ingredients.py
==============================
Convert data/ingredients.xlsx -> data/ingredients.csv.

Run this whenever the spreadsheet changes:
    python scripts/export_ingredients.py

Requires openpyxl (already in .venv):
    .venv/bin/python scripts/export_ingredients.py
"""

import csv
from pathlib import Path

import openpyxl

DATA = Path(__file__).parent.parent / "data"
XLSX = DATA / "ingredients.xlsx"
CSV  = DATA / "ingredients.csv"


def export():
    wb = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)
    ws = wb.active

    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise ValueError(f"No data found in {XLSX}")

    header, data_rows = rows[0], rows[1:]

    # Drop fully empty rows (common Excel artifact)
    data_rows = [r for r in data_rows if any(v is not None for v in r)]

    with open(CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(data_rows)

    print(f"Wrote {len(data_rows)} ingredients to {CSV}")


if __name__ == "__main__":
    export()
