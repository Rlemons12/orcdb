"""Load the drawing workbook into the BOM.db drawing table."""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


DEFAULT_WORKBOOK = "data/Active Drawing List breakdown.xlsx"
DEFAULT_SHEET = "drawings_data"
DEFAULT_DB = "data/BOM.db"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load the drawings_data worksheet into the drawing table."
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--workbook",
        default=DEFAULT_WORKBOOK,
        help="Excel workbook path.",
    )
    parser.add_argument(
        "--sheet",
        default=DEFAULT_SHEET,
        help="Worksheet name. Leading/trailing spaces are ignored when matching.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a timestamped database backup before updating.",
    )
    return parser.parse_args()


def make_backup(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(
        f"{db_path.stem}_before_drawing_load_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def normalize_column_name(column_name: object) -> str:
    value = str(column_name).strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = value.strip("_")
    if not value:
        value = "column"
    if value[0].isdigit():
        value = f"col_{value}"
    return value


def normalize_columns(columns: list[object]) -> list[str]:
    seen: dict[str, int] = {}
    normalized = []
    for column in columns:
        base = normalize_column_name(column)
        count = seen.get(base, 0)
        seen[base] = count + 1
        normalized.append(base if count == 0 else f"{base}_{count + 1}")
    return normalized


def matching_sheet(workbook_path: Path, requested_sheet: str) -> str:
    workbook = pd.ExcelFile(workbook_path)
    requested = requested_sheet.strip()
    for sheet_name in workbook.sheet_names:
        if sheet_name.strip() == requested:
            return sheet_name
    raise SystemExit(
        f"Worksheet not found: {requested_sheet!r}. Available: {workbook.sheet_names}"
    )


def read_drawings(workbook_path: Path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(workbook_path, sheet_name=sheet_name, dtype=object)
    df.columns = normalize_columns(list(df.columns))
    df = df.where(pd.notna(df), None)
    for column in df.columns:
        df[column] = df[column].map(
            lambda value: value.strip() if isinstance(value, str) else value
        )
    return df


def create_table(connection: sqlite3.Connection, columns: list[str]) -> None:
    column_sql = ",\n            ".join(f"{column} TEXT" for column in columns)
    connection.execute("DROP TABLE IF EXISTS drawing")
    connection.execute(
        f"""
        CREATE TABLE drawing (
            {column_sql}
        )
        """
    )


def load_table(connection: sqlite3.Connection, df: pd.DataFrame) -> None:
    columns = list(df.columns)
    create_table(connection, columns)
    placeholders = ", ".join("?" for _ in columns)
    column_list = ", ".join(columns)
    rows = [tuple(None if pd.isna(value) else value for value in row) for row in df.itertuples(index=False, name=None)]
    connection.executemany(
        f"INSERT INTO drawing ({column_list}) VALUES ({placeholders})",
        rows,
    )
    for column in ("area", "equipment_group", "model", "asset_number", "drawing_number"):
        if column in columns:
            connection.execute(f"CREATE INDEX idx_drawing_{column} ON drawing ({column})")
    connection.commit()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    workbook_path = Path(args.workbook)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")
    if not workbook_path.exists():
        raise SystemExit(f"Workbook does not exist: {workbook_path}")

    backup_path = None
    if not args.no_backup:
        backup_path = make_backup(db_path)

    sheet_name = matching_sheet(workbook_path, args.sheet)
    df = read_drawings(workbook_path, sheet_name)

    with sqlite3.connect(db_path) as connection:
        load_table(connection, df)
        row_count = connection.execute("SELECT COUNT(*) FROM drawing").fetchone()[0]
        columns = [row[1] for row in connection.execute("PRAGMA table_info(drawing)")]

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Workbook: {workbook_path}")
    print(f"Sheet loaded: {sheet_name!r}")
    print(f"drawing rows: {row_count}")
    print(f"drawing columns: {', '.join(columns)}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
