"""Create and populate the position table from the normalized hierarchy."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create position rows from area -> equipment_group -> model -> asset_number."
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
        f"{db_path.stem}_before_position_table_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


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


def require_tables(connection: sqlite3.Connection) -> None:
    missing = [
        table_name
        for table_name in ("area", "equipment_group", "model", "asset_number")
        if not table_exists(connection, table_name)
    ]
    if missing:
        raise SystemExit(f"Missing required table(s): {missing}")


def rebuild_position(connection: sqlite3.Connection) -> None:
    require_tables(connection)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("DROP TABLE IF EXISTS position")
    connection.execute(
        """
        CREATE TABLE position (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_id INTEGER,
            equipment_group_id INTEGER,
            model_id INTEGER,
            asset_number_id INTEGER,
            location_id INTEGER,
            subassembly_id INTEGER,
            component_assembly_id INTEGER,
            assembly_view_id INTEGER,
            site_location_id INTEGER,
            campus_id INTEGER,
            building_id INTEGER,
            FOREIGN KEY (area_id)
                REFERENCES area (area_id),
            FOREIGN KEY (equipment_group_id)
                REFERENCES equipment_group (equipment_group_id),
            FOREIGN KEY (model_id)
                REFERENCES model (model_id),
            FOREIGN KEY (asset_number_id)
                REFERENCES asset_number (asset_number_id),
            UNIQUE (asset_number_id)
        )
        """
    )
    connection.execute(
        """
        INSERT INTO position (
            area_id,
            equipment_group_id,
            model_id,
            asset_number_id
        )
        SELECT
            a.area_id,
            eg.equipment_group_id,
            m.model_id,
            an.asset_number_id
        FROM asset_number an
        LEFT JOIN model m
          ON m.model_id = an.model_id
        LEFT JOIN equipment_group eg
          ON eg.equipment_group_id = m.equipment_group_id
        LEFT JOIN area a
          ON a.area_id = eg.area_id
        ORDER BY
            a.area,
            eg.equipment_group,
            m.model,
            an.asset_number
        """
    )
    connection.execute("CREATE INDEX idx_position_area_id ON position (area_id)")
    connection.execute(
        "CREATE INDEX idx_position_equipment_group_id ON position (equipment_group_id)"
    )
    connection.execute("CREATE INDEX idx_position_model_id ON position (model_id)")
    connection.execute(
        "CREATE INDEX idx_position_asset_number_id ON position (asset_number_id)"
    )
    connection.commit()


def print_validation(connection: sqlite3.Connection) -> None:
    checks = [
        ("position rows", "SELECT COUNT(*) FROM position"),
        ("asset_number rows", "SELECT COUNT(*) FROM asset_number"),
        (
            "position rows missing model_id",
            "SELECT COUNT(*) FROM position WHERE model_id IS NULL",
        ),
        (
            "position area orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM position p
            LEFT JOIN area a
              ON a.area_id = p.area_id
            WHERE p.area_id IS NOT NULL
              AND a.area_id IS NULL
            """,
        ),
        (
            "position equipment_group orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM position p
            LEFT JOIN equipment_group eg
              ON eg.equipment_group_id = p.equipment_group_id
            WHERE p.equipment_group_id IS NOT NULL
              AND eg.equipment_group_id IS NULL
            """,
        ),
        (
            "position model orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM position p
            LEFT JOIN model m
              ON m.model_id = p.model_id
            WHERE p.model_id IS NOT NULL
              AND m.model_id IS NULL
            """,
        ),
        (
            "position asset_number orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM position p
            LEFT JOIN asset_number an
              ON an.asset_number_id = p.asset_number_id
            WHERE p.asset_number_id IS NOT NULL
              AND an.asset_number_id IS NULL
            """,
        ),
        ("foreign_key_check rows", "SELECT COUNT(*) FROM pragma_foreign_key_check"),
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
        rebuild_position(connection)
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
