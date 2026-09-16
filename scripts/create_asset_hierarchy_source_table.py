"""Create a deduplicated asset hierarchy source table from BOM rows."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


DEFAULT_DB = "data/BOM.db"
DEFAULT_TABLE = "asset_hierarchy_source"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deduplicated hierarchy source table from boms_for_department "
            "using department_code, asset_number with a leading AU- removed, "
            "and asset_description."
        )
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help="Output table name to rebuild.",
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
        f"{db_path.stem}_before_asset_hierarchy_source_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def require_source_table(connection: sqlite3.Connection) -> None:
    exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'boms_for_department'
        """
    ).fetchone()
    if not exists:
        raise SystemExit("Missing source table: boms_for_department")


def validate_table_name(table_name: str) -> None:
    if not table_name.replace("_", "").isalnum() or table_name[0].isdigit():
        raise SystemExit(f"Invalid table name: {table_name}")


def rebuild_table(connection: sqlite3.Connection, table_name: str) -> int:
    validate_table_name(table_name)
    connection.execute(f"DROP TABLE IF EXISTS {table_name}")
    connection.execute(
        f"""
        CREATE TABLE {table_name} (
            area TEXT NOT NULL,
            asset_number TEXT NOT NULL,
            asset_description TEXT,
            UNIQUE (area, asset_number)
        )
        """
    )
    connection.execute(
        f"""
        INSERT INTO {table_name} (
            area,
            asset_number,
            asset_description
        )
        SELECT DISTINCT
            TRIM(department_code) AS area,
            CASE
                WHEN TRIM(asset_number) LIKE 'AU-%'
                    THEN SUBSTR(TRIM(asset_number), 4)
                ELSE TRIM(asset_number)
            END AS asset_number,
            NULLIF(TRIM(asset_description), '') AS asset_description
        FROM boms_for_department
        WHERE NULLIF(TRIM(department_code), '') IS NOT NULL
          AND NULLIF(TRIM(asset_number), '') IS NOT NULL
        ORDER BY
            area,
            asset_number
        """
    )
    connection.execute(
        f"CREATE INDEX idx_{table_name}_area ON {table_name} (area)"
    )
    connection.execute(
        f"CREATE INDEX idx_{table_name}_asset_number ON {table_name} (asset_number)"
    )
    connection.commit()
    return connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]


def print_validation(connection: sqlite3.Connection, table_name: str) -> None:
    source_rows = connection.execute("SELECT COUNT(*) FROM boms_for_department").fetchone()[0]
    distinct_rows = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
    blank_descriptions = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE asset_description IS NULL
        """
    ).fetchone()[0]
    duplicate_keys = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT area, asset_number
            FROM {table_name}
            GROUP BY area, asset_number
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]
    print(f"source boms_for_department rows: {source_rows}")
    print(f"{table_name} rows: {distinct_rows}")
    print(f"{table_name} rows missing description: {blank_descriptions}")
    print(f"{table_name} duplicate area+asset_number keys: {duplicate_keys}")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    backup_path = None
    if not args.no_backup:
        backup_path = make_backup(db_path)

    with sqlite3.connect(db_path) as connection:
        require_source_table(connection)
        rebuild_table(connection, args.table)
        print_validation(connection, args.table)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
