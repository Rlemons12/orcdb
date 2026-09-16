"""Remove leading AU- prefixes from BOM asset group and asset number values."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Remove the leading AU- prefix from asset group and asset number values in BOM.db."
    )
    parser.add_argument(
        "--db",
        default="data/BOM.db",
        help="SQLite database path to update.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a timestamped database backup before updating.",
    )
    return parser.parse_args()


def table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    return (
        connection.execute(
            """
            SELECT 1
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()
        is not None
    )


def count_prefixed(connection: sqlite3.Connection, table_name: str, column_name: str) -> int:
    if not table_exists(connection, table_name):
        return 0
    return connection.execute(
        f"SELECT COUNT(*) FROM {table_name} WHERE {column_name} LIKE 'AU-%'"
    ).fetchone()[0]


def remove_prefix(connection: sqlite3.Connection, table_name: str, column_name: str) -> int:
    if not table_exists(connection, table_name):
        return 0
    before = count_prefixed(connection, table_name, column_name)
    connection.execute(
        f"""
        UPDATE {table_name}
        SET {column_name} = SUBSTR({column_name}, 4)
        WHERE {column_name} LIKE 'AU-%'
        """
    )
    return before


def check_duplicate_risk(connection: sqlite3.Connection) -> None:
    checks = []
    if table_exists(connection, "equipment_group"):
        checks.append(
            (
                "equipment_group",
                """
                SELECT area_id, normalized_equipment_group, COUNT(*)
                FROM (
                    SELECT
                        area_id,
                        CASE
                            WHEN equipment_group LIKE 'AU-%' THEN SUBSTR(equipment_group, 4)
                            ELSE equipment_group
                        END AS normalized_equipment_group
                    FROM equipment_group
                )
                GROUP BY area_id, normalized_equipment_group
                HAVING COUNT(*) > 1
                """,
            )
        )
    if table_exists(connection, "asset_number"):
        checks.append(
            (
                "asset_number",
                """
                SELECT model_id, normalized_asset_number, COUNT(*)
                FROM (
                    SELECT
                        model_id,
                        CASE
                            WHEN asset_number LIKE 'AU-%' THEN SUBSTR(asset_number, 4)
                            ELSE asset_number
                        END AS normalized_asset_number
                    FROM asset_number
                )
                GROUP BY model_id, normalized_asset_number
                HAVING COUNT(*) > 1
                """,
            )
        )

    for table_name, query in checks:
        rows = connection.execute(query).fetchall()
        if rows:
            sample = rows[:10]
            raise SystemExit(
                f"Removing AU- would create duplicate keys in {table_name}. Sample: {sample}"
            )


def make_backup(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(f"{db_path.stem}_before_remove_au_prefix_{stamp}{db_path.suffix}")
    shutil.copy2(db_path, backup_path)
    return backup_path


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    backup_path = None
    if not args.no_backup:
        backup_path = make_backup(db_path)

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        check_duplicate_risk(connection)
        updates = [
            ("boms_for_department", "asset_group_item"),
            ("boms_for_department", "asset_number"),
            ("equipment_group", "equipment_group"),
            ("asset_number", "asset_number"),
        ]
        results = []
        for table_name, column_name in updates:
            changed = remove_prefix(connection, table_name, column_name)
            results.append((table_name, column_name, changed))
        connection.commit()

    if backup_path:
        print(f"Backup created: {backup_path}")
    for table_name, column_name, changed in results:
        print(f"{table_name}.{column_name}: removed AU- from {changed} row(s)")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
