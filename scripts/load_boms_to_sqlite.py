"""Load configured BOM department CSV exports into a local SQLite database."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


EXPECTED_COLUMNS = [
    "DEPARTMENT_CODE",
    "MATCHED_OPERATION_SEQ",
    "ASSET_NUMBER",
    "ASSET_DESCRIPTION",
    "ASSET_GROUP_ITEM",
    "ASSET_GROUP_DESCRIPTION",
    "BILL_SEQUENCE_ID",
    "COMMON_BILL_SEQUENCE_ID",
    "ALTERNATE_BOM_DESIGNATOR",
    "ASSEMBLY_TYPE",
    "ITEM_NUM",
    "COMPONENT_SEQUENCE_ID",
    "PART_NUMBER",
    "PART_DESCRIPTION",
    "COMPONENT_QUANTITY",
    "COMPONENT_UOM",
    "COMPONENT_YIELD_FACTOR",
    "COMPONENT_REMARKS",
    "EFFECTIVITY_DATE",
    "DISABLE_DATE",
    "CURRENTLY_ACTIVE",
]

OUTPUT_PATTERN = re.compile(
    r"^configured_boms_for_department_(?P<department>.+)_(?P<stamp>\d{8}_\d{6})\.csv$",
    re.IGNORECASE,
)

TABLE_NAME = "boms_for_department"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the latest valid configured BOM CSV for each department into SQLite."
    )
    parser.add_argument(
        "--input-dir",
        default="outputs/configured_boms_for_department",
        help="Folder containing configured_boms_for_department_*.csv files.",
    )
    parser.add_argument(
        "--db",
        default="data/BOM.db",
        help="SQLite database path to create/update.",
    )
    parser.add_argument(
        "--summary-dir",
        default="outputs/configured_boms_for_department",
        help="Folder where the load summary CSV will be written.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=50000,
        help="CSV rows to load per batch.",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to the existing table instead of replacing it.",
    )
    return parser.parse_args()


def csv_header(path: Path) -> list[str] | None:
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return next(csv.reader(handle))
    except (OSError, StopIteration, UnicodeDecodeError, csv.Error):
        return None


def discover_latest_valid_files(input_dir: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    selected: dict[str, dict[str, object]] = {}
    rejected: list[dict[str, object]] = []

    for path in sorted(input_dir.glob("configured_boms_for_department_*.csv")):
        match = OUTPUT_PATTERN.match(path.name)
        if not match:
            rejected.append({"file": str(path), "reason": "filename did not match expected pattern"})
            continue

        header = csv_header(path)
        if header != EXPECTED_COLUMNS:
            rejected.append({"file": str(path), "reason": "invalid or missing configured BOM CSV header"})
            continue

        department = match.group("department").upper()
        stamp = match.group("stamp")
        candidate = {
            "department": department,
            "stamp": stamp,
            "path": path,
            "size_bytes": path.stat().st_size,
        }
        current = selected.get(department)
        if current is None or stamp > str(current["stamp"]):
            selected[department] = candidate

    return sorted(selected.values(), key=lambda item: str(item["department"])), rejected


def create_table(connection: sqlite3.Connection, replace: bool) -> None:
    columns_sql = ",\n        ".join(f"{column.lower()} TEXT" for column in EXPECTED_COLUMNS)
    if replace:
        connection.execute(f"DROP TABLE IF EXISTS {TABLE_NAME}")

    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            {columns_sql},
            source_file TEXT NOT NULL,
            loaded_at_utc TEXT NOT NULL
        )
        """
    )
    connection.commit()


def load_file(
    connection: sqlite3.Connection,
    path: Path,
    chunk_size: int,
    loaded_at_utc: str,
) -> int:
    rows_loaded = 0

    for chunk in pd.read_csv(
        path,
        dtype=str,
        keep_default_na=False,
        chunksize=chunk_size,
        encoding="utf-8-sig",
    ):
        chunk.columns = [column.lower() for column in chunk.columns]
        chunk["source_file"] = path.name
        chunk["loaded_at_utc"] = loaded_at_utc
        chunk.to_sql(TABLE_NAME, connection, if_exists="append", index=False)
        rows_loaded += len(chunk)

    return rows_loaded


def create_indexes(connection: sqlite3.Connection) -> None:
    index_columns = [
        "department_code",
        "asset_number",
        "asset_group_item",
        "part_number",
        "bill_sequence_id",
    ]
    for column in index_columns:
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_{column} ON {TABLE_NAME} ({column})"
        )
    connection.commit()


def write_summary(summary_dir: Path, loaded: list[dict[str, object]], rejected: list[dict[str, object]]) -> Path:
    summary_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = summary_dir / f"bom_sql_load_summary_{stamp}.csv"

    rows = []
    for item in loaded:
        rows.append(
            {
                "status": "loaded",
                "department": item["department"],
                "file": item["file"],
                "rows": item["rows"],
                "reason": "",
            }
        )
    for item in rejected:
        rows.append(
            {
                "status": "rejected",
                "department": "",
                "file": item["file"],
                "rows": "",
                "reason": item["reason"],
            }
        )

    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["status", "department", "file", "rows", "reason"])
        writer.writeheader()
        writer.writerows(rows)

    return summary_path


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    db_path = Path(args.db)
    summary_dir = Path(args.summary_dir)

    if not input_dir.exists():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    files, rejected = discover_latest_valid_files(input_dir)
    if not files:
        raise SystemExit(f"No valid configured BOM CSV files found in {input_dir}")

    db_path.parent.mkdir(parents=True, exist_ok=True)
    loaded_at_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    loaded: list[dict[str, object]] = []

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
        create_table(connection, replace=not args.append)

        for item in files:
            path = Path(item["path"])
            rows_loaded = load_file(connection, path, args.chunk_size, loaded_at_utc)
            loaded.append(
                {
                    "department": item["department"],
                    "file": str(path),
                    "rows": rows_loaded,
                }
            )
            print(f"Loaded {rows_loaded:>8} rows from {path.name}")

        create_indexes(connection)

    summary_path = write_summary(summary_dir, loaded, rejected)
    total_rows = sum(int(item["rows"]) for item in loaded)
    print(f"Loaded {total_rows} total rows into {db_path} table {TABLE_NAME}")
    print(f"Wrote load summary: {summary_path}")
    if rejected:
        print(f"Rejected {len(rejected)} invalid CSV file(s)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
