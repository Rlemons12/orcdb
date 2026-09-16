"""Restore asset_number_id and use it from position."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add asset_number_id to asset_number and position."
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
        f"{db_path.stem}_before_asset_number_id_restore_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def columns_for(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def rebuild_tables(connection: sqlite3.Connection) -> None:
    asset_columns = columns_for(connection, "asset_number")
    position_columns = columns_for(connection, "position")
    if {"model_id", "asset_number", "asset_description"} - asset_columns:
        raise SystemExit("asset_number is missing required hierarchy columns")
    if {"id", "area_id", "equipment_group_id", "model_id"} - position_columns:
        raise SystemExit("position is missing required hierarchy columns")
    if "asset_number" not in position_columns and "asset_number_id" not in position_columns:
        raise SystemExit("position must contain asset_number or asset_number_id")

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS asset_number_new")
    connection.execute("DROP TABLE IF EXISTS position_new")
    connection.execute(
        """
        CREATE TABLE asset_number_new (
            asset_number_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_id INTEGER,
            asset_number TEXT NOT NULL,
            asset_description TEXT,
            FOREIGN KEY (model_id)
                REFERENCES model (model_id),
            UNIQUE (model_id, asset_number)
        )
        """
    )
    if "asset_number_id" in asset_columns:
        connection.execute(
            """
            INSERT INTO asset_number_new (
                asset_number_id,
                model_id,
                asset_number,
                asset_description
            )
            SELECT
                asset_number_id,
                model_id,
                asset_number,
                asset_description
            FROM asset_number
            ORDER BY asset_number_id
            """
        )
    else:
        connection.execute(
            """
            INSERT INTO asset_number_new (
                model_id,
                asset_number,
                asset_description
            )
            SELECT
                model_id,
                asset_number,
                asset_description
            FROM asset_number
            ORDER BY
                model_id IS NULL,
                model_id,
                asset_number
            """
        )

    connection.execute(
        """
        CREATE TABLE position_new (
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
                REFERENCES asset_number_new (asset_number_id),
            UNIQUE (asset_number_id)
        )
        """
    )
    if "asset_number_id" in position_columns:
        connection.execute(
            """
            INSERT INTO position_new (
                id,
                area_id,
                equipment_group_id,
                model_id,
                asset_number_id,
                location_id,
                subassembly_id,
                component_assembly_id,
                assembly_view_id,
                site_location_id,
                campus_id,
                building_id
            )
            SELECT
                id,
                area_id,
                equipment_group_id,
                model_id,
                asset_number_id,
                location_id,
                subassembly_id,
                component_assembly_id,
                assembly_view_id,
                site_location_id,
                campus_id,
                building_id
            FROM position
            ORDER BY id
            """
        )
    else:
        connection.execute(
            """
            INSERT INTO position_new (
                id,
                area_id,
                equipment_group_id,
                model_id,
                asset_number_id,
                location_id,
                subassembly_id,
                component_assembly_id,
                assembly_view_id,
                site_location_id,
                campus_id,
                building_id
            )
            SELECT
                p.id,
                p.area_id,
                p.equipment_group_id,
                p.model_id,
                an.asset_number_id,
                p.location_id,
                p.subassembly_id,
                p.component_assembly_id,
                p.assembly_view_id,
                p.site_location_id,
                p.campus_id,
                p.building_id
            FROM position p
            LEFT JOIN asset_number_new an
              ON an.asset_number = p.asset_number
             AND (
                    an.model_id = p.model_id
                 OR (an.model_id IS NULL AND p.model_id IS NULL)
             )
            ORDER BY p.id
            """
        )

    connection.execute("DROP TABLE position")
    connection.execute("DROP TABLE asset_number")
    connection.execute("ALTER TABLE asset_number_new RENAME TO asset_number")
    connection.execute("ALTER TABLE position_new RENAME TO position")
    connection.execute("CREATE INDEX idx_asset_number_model_id ON asset_number (model_id)")
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number ON asset_number (asset_number)"
    )
    connection.execute("CREATE INDEX idx_position_area_id ON position (area_id)")
    connection.execute(
        "CREATE INDEX idx_position_equipment_group_id ON position (equipment_group_id)"
    )
    connection.execute("CREATE INDEX idx_position_model_id ON position (model_id)")
    connection.execute(
        "CREATE INDEX idx_position_asset_number_id ON position (asset_number_id)"
    )
    connection.execute("PRAGMA foreign_keys = ON")
    connection.commit()


def print_validation(connection: sqlite3.Connection) -> None:
    checks = [
        ("asset_number rows", "SELECT COUNT(*) FROM asset_number"),
        ("position rows", "SELECT COUNT(*) FROM position"),
        (
            "position missing asset_number_id",
            "SELECT COUNT(*) FROM position WHERE asset_number_id IS NULL",
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
        (
            "drawing position orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM drawing d
            LEFT JOIN position p
              ON p.id = d.position_id
            WHERE d.position_id IS NOT NULL
              AND p.id IS NULL
            """,
        ),
        (
            "bom position orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM bom b
            LEFT JOIN position p
              ON p.id = b.position_id
            WHERE b.position_id IS NOT NULL
              AND p.id IS NULL
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
        rebuild_tables(connection)
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
