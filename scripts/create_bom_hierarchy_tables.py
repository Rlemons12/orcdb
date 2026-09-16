"""Create area -> equipment_group -> asset_number staging tables in BOM.db."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build area, equipment_group, and asset_number staging tables "
            "from boms_for_department."
        )
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
    connection.execute("DROP TABLE IF EXISTS model")
    connection.execute("DROP TABLE IF EXISTS equipment_group")
    connection.execute("DROP TABLE IF EXISTS area")

    connection.execute(
        """
        CREATE TABLE area (
            area_id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT NOT NULL UNIQUE
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE equipment_group (
            equipment_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_id INTEGER NOT NULL,
            equipment_group TEXT NOT NULL,
            equipment_group_description TEXT,
            FOREIGN KEY (area_id)
                REFERENCES area (area_id),
            UNIQUE (area_id, equipment_group)
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
        INSERT INTO area (area)
        SELECT department_code
        FROM boms_for_department
        WHERE NULLIF(department_code, '') IS NOT NULL
        GROUP BY department_code
        ORDER BY department_code
        """
    )

    connection.execute(
        """
        INSERT INTO equipment_group (
            area_id,
            equipment_group,
            equipment_group_description
        )
        SELECT
            a.area_id,
            src.asset_group_item,
            MAX(NULLIF(src.asset_group_description, '')) AS equipment_group_description
        FROM boms_for_department src
        JOIN area a
          ON a.area = src.department_code
        WHERE NULLIF(src.department_code, '') IS NOT NULL
          AND NULLIF(src.asset_group_item, '') IS NOT NULL
        GROUP BY
            a.area_id,
            src.asset_group_item
        ORDER BY
            a.area_id,
            src.asset_group_item
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
        JOIN area a
          ON a.area = src.department_code
        JOIN equipment_group eg
          ON eg.area_id = a.area_id
         AND eg.equipment_group = src.asset_group_item
        WHERE NULLIF(src.department_code, '') IS NOT NULL
          AND NULLIF(src.asset_group_item, '') IS NOT NULL
          AND NULLIF(src.asset_number, '') IS NOT NULL
        GROUP BY
            eg.equipment_group_id,
            src.asset_number
        ORDER BY
            eg.equipment_group_id,
            src.asset_number
        """
    )

    connection.execute("CREATE INDEX idx_equipment_group_area_id ON equipment_group (area_id)")
    connection.execute(
        "CREATE INDEX idx_equipment_group_equipment_group "
        "ON equipment_group (equipment_group)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_equipment_group_id "
        "ON asset_number (equipment_group_id)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number ON asset_number (asset_number)"
    )
    connection.commit()


def print_counts(connection: sqlite3.Connection) -> None:
    checks = [
        ("area rows", "SELECT COUNT(*) FROM area"),
        ("equipment_group rows", "SELECT COUNT(*) FROM equipment_group"),
        ("asset_number rows", "SELECT COUNT(*) FROM asset_number"),
        (
            "equipment_group orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM equipment_group eg
            LEFT JOIN area a
              ON a.area_id = eg.area_id
            WHERE a.area_id IS NULL
            """,
        ),
        (
            "asset_number orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM asset_number an
            LEFT JOIN equipment_group eg
              ON eg.equipment_group_id = an.equipment_group_id
            WHERE eg.equipment_group_id IS NULL
            """,
        ),
    ]
    for label, query in checks:
        value = connection.execute(query).fetchone()[0]
        print(f"{label}: {value}")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    with sqlite3.connect(db_path) as connection:
        require_source_table(connection)
        rebuild_tables(connection)
        print_counts(connection)

    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
