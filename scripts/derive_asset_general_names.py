"""Derive generalized asset names on asset_hierarchy_source."""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from create_general_asset_description import generalize_description


FILLER_SUFFIX_RE = re.compile(
    r"\bFOR\s+(?:AUTOMATIC\s+|MANUAL\s+)?FILLERS?(?:\s+\d+(?:\s*-\s*\d+)?)?\b"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate asset_hierarchy_source.general_asset_name."
    )
    parser.add_argument("--db", default="data/BOM.db", help="SQLite database path.")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a timestamped database backup before updating.",
    )
    return parser.parse_args()


def make_backup(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(
        f"{db_path.stem}_before_general_asset_names_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def columns_for(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def derive_general_asset_name(asset_description: str | None) -> str | None:
    value = generalize_description(asset_description)
    if not value:
        return None

    value = FILLER_SUFFIX_RE.sub(" ", value)
    value = re.sub(r"\s+", " ", value).strip(" ,.-")
    return value or None


def ensure_column(connection: sqlite3.Connection) -> None:
    columns = columns_for(connection, "asset_hierarchy_source")
    if "general_asset_name" not in columns:
        connection.execute(
            "ALTER TABLE asset_hierarchy_source ADD COLUMN general_asset_name TEXT"
        )


def update_general_asset_names(connection: sqlite3.Connection) -> int:
    ensure_column(connection)
    rows = connection.execute(
        """
        SELECT
            rowid,
            asset_description
        FROM asset_hierarchy_source
        """
    ).fetchall()
    updates = [
        (derive_general_asset_name(asset_description), rowid)
        for rowid, asset_description in rows
    ]
    connection.executemany(
        """
        UPDATE asset_hierarchy_source
        SET general_asset_name = ?
        WHERE rowid = ?
        """,
        updates,
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_asset_hierarchy_source_general_asset_name
        ON asset_hierarchy_source (general_asset_name)
        """
    )
    connection.commit()
    return len(updates)


def print_validation(connection: sqlite3.Connection) -> None:
    checks = [
        ("asset_hierarchy_source rows", "SELECT COUNT(*) FROM asset_hierarchy_source"),
        (
            "rows with general_asset_name",
            """
            SELECT COUNT(*)
            FROM asset_hierarchy_source
            WHERE general_asset_name IS NOT NULL
              AND TRIM(general_asset_name) <> ''
            """,
        ),
        (
            "distinct general_asset_name",
            """
            SELECT COUNT(DISTINCT general_asset_name)
            FROM asset_hierarchy_source
            WHERE general_asset_name IS NOT NULL
              AND TRIM(general_asset_name) <> ''
            """,
        ),
    ]
    for label, query in checks:
        print(f"{label}: {connection.execute(query).fetchone()[0]}")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    backup_path = None
    if not args.no_backup:
        backup_path = make_backup(db_path)

    with sqlite3.connect(db_path) as connection:
        updated = update_general_asset_names(connection)
        print(f"asset_hierarchy_source rows updated: {updated}")
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
