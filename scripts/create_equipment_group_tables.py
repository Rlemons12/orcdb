"""Create normalized equipment group and asset number tables in BOM.db."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build equipment_group and asset_number tables from boms_for_department."
    )
    parser.add_argument(
        "--db",
        default="data/BOM.db",
        help="SQLite database path containing boms_for_department.",
    )
    return parser.parse_args()


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


def rebuild_tables(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("DROP TABLE IF EXISTS asset_number")
    connection.execute("DROP TABLE IF EXISTS equipment_group")

    connection.execute(
        """
        CREATE TABLE equipment_group (
            equipment_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_group TEXT NOT NULL UNIQUE,
            equipment_group_description TEXT
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE asset_number (
            equipment_group_id INTEGER NOT NULL,
            asset_number TEXT NOT NULL,
            asset_description TEXT,
            FOREIGN KEY (equipment_group_id)
                REFERENCES equipment_group (equipment_group_id),
            UNIQUE (equipment_group_id, asset_number)
        )
        """
    )

    connection.execute(
        """
        INSERT INTO equipment_group (
            equipment_group,
            equipment_group_description
        )
        SELECT
            asset_group_item AS equipment_group,
            MAX(NULLIF(asset_group_description, '')) AS equipment_group_description
        FROM boms_for_department
        WHERE NULLIF(asset_group_item, '') IS NOT NULL
        GROUP BY asset_group_item
        ORDER BY asset_group_item
        """
    )

    connection.execute(
        """
        INSERT INTO asset_number (
            equipment_group_id,
            asset_number,
            asset_description
        )
        SELECT
            eg.equipment_group_id,
            src.asset_number,
            MAX(NULLIF(src.asset_description, '')) AS asset_description
        FROM boms_for_department src
        JOIN equipment_group eg
          ON eg.equipment_group = src.asset_group_item
        WHERE NULLIF(src.asset_group_item, '') IS NOT NULL
          AND NULLIF(src.asset_number, '') IS NOT NULL
        GROUP BY
            eg.equipment_group_id,
            src.asset_number
        ORDER BY
            eg.equipment_group_id,
            src.asset_number
        """
    )

    connection.execute(
        "CREATE INDEX idx_asset_number_equipment_group_id ON asset_number (equipment_group_id)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number ON asset_number (asset_number)"
    )
    connection.execute(
        "CREATE INDEX idx_equipment_group_equipment_group ON equipment_group (equipment_group)"
    )
    connection.commit()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    with sqlite3.connect(db_path) as connection:
        require_source_table(connection)
        rebuild_tables(connection)
        equipment_group_count = connection.execute(
            "SELECT COUNT(*) FROM equipment_group"
        ).fetchone()[0]
        asset_number_count = connection.execute(
            "SELECT COUNT(*) FROM asset_number"
        ).fetchone()[0]
        orphan_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM asset_number an
            LEFT JOIN equipment_group eg
              ON eg.equipment_group_id = an.equipment_group_id
            WHERE eg.equipment_group_id IS NULL
            """
        ).fetchone()[0]

    print(f"equipment_group rows: {equipment_group_count}")
    print(f"asset_number rows: {asset_number_count}")
    print(f"asset_number orphan foreign keys: {orphan_count}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
