import csv
from io import StringIO
from pathlib import Path


def load_csv_rows(path: str) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def load_csv_rows_from_text(csv_text: str) -> list[dict[str, str]]:
    handle = StringIO(csv_text)
    return list(csv.DictReader(handle))
