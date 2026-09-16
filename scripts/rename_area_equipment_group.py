"""Rename department_code/asset_group hierarchy tables to area/equipment_group."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rename department_code -> area and asset_group -> equipment_group "
            "in the normalized BOM hierarchy."
        )
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
        f"{db_path.stem}_before_area_equipment_group_rename_{stamp}{db_path.suffix}"
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


def columns_for(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def first_existing(columns: set[str], choices: tuple[str, ...], table_name: str) -> str:
    for choice in choices:
        if choice in columns:
            return choice
    raise SystemExit(f"{table_name} is missing one of: {choices}")


def rebuild_hierarchy(connection: sqlite3.Connection) -> None:
    area_source = "area" if table_exists(connection, "area") else "department_code"
    group_source = (
        "equipment_group" if table_exists(connection, "equipment_group") else "asset_group"
    )
    for table_name in (area_source, group_source, "model", "asset_number"):
        if not table_exists(connection, table_name):
            raise SystemExit(f"Missing required table: {table_name}")

    area_columns = columns_for(connection, area_source)
    group_columns = columns_for(connection, group_source)
    model_columns = columns_for(connection, "model")

    area_pk = first_existing(area_columns, ("area_id", "department_code_id"), area_source)
    area_value = first_existing(area_columns, ("area", "department_code"), area_source)
    group_pk = first_existing(
        group_columns, ("equipment_group_id", "asset_group_id"), group_source
    )
    group_area_fk = first_existing(
        group_columns, ("area_id", "department_code_id"), group_source
    )
    group_value = first_existing(
        group_columns, ("equipment_group", "asset_group_item"), group_source
    )
    group_description = first_existing(
        group_columns,
        ("equipment_group_description", "asset_group_description"),
        group_source,
    )
    model_group_fk = first_existing(
        model_columns, ("equipment_group_id", "asset_group_id"), "model"
    )

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS asset_number_new")
    connection.execute("DROP TABLE IF EXISTS model_new")
    connection.execute("DROP TABLE IF EXISTS equipment_group_new")
    connection.execute("DROP TABLE IF EXISTS area_new")

    connection.execute(
        """
        CREATE TABLE area_new (
            area_id INTEGER PRIMARY KEY AUTOINCREMENT,
            area TEXT NOT NULL UNIQUE
        )
        """
    )
    connection.execute(
        f"""
        INSERT INTO area_new (area_id, area)
        SELECT {area_pk}, {area_value}
        FROM {area_source}
        """
    )

    connection.execute(
        """
        CREATE TABLE equipment_group_new (
            equipment_group_id INTEGER PRIMARY KEY AUTOINCREMENT,
            area_id INTEGER NOT NULL,
            equipment_group TEXT NOT NULL,
            equipment_group_description TEXT,
            FOREIGN KEY (area_id)
                REFERENCES area_new (area_id),
            UNIQUE (area_id, equipment_group)
        )
        """
    )
    connection.execute(
        f"""
        INSERT INTO equipment_group_new (
            equipment_group_id,
            area_id,
            equipment_group,
            equipment_group_description
        )
        SELECT
            {group_pk},
            {group_area_fk},
            {group_value},
            {group_description}
        FROM {group_source}
        """
    )

    connection.execute(
        """
        CREATE TABLE model_new (
            model_id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_group_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            FOREIGN KEY (equipment_group_id)
                REFERENCES equipment_group_new (equipment_group_id),
            UNIQUE (equipment_group_id, model)
        )
        """
    )
    connection.execute(
        f"""
        INSERT INTO model_new (
            model_id,
            equipment_group_id,
            model
        )
        SELECT
            model_id,
            {model_group_fk},
            model
        FROM model
        """
    )

    connection.execute(
        """
        CREATE TABLE asset_number_new (
            model_id INTEGER,
            asset_number TEXT NOT NULL,
            asset_description TEXT,
            FOREIGN KEY (model_id)
                REFERENCES model_new (model_id),
            UNIQUE (model_id, asset_number)
        )
        """
    )
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
        """
    )

    connection.execute("DROP TABLE asset_number")
    connection.execute("DROP TABLE model")
    connection.execute(f"DROP TABLE {group_source}")
    connection.execute(f"DROP TABLE {area_source}")
    connection.execute("ALTER TABLE area_new RENAME TO area")
    connection.execute("ALTER TABLE equipment_group_new RENAME TO equipment_group")
    connection.execute("ALTER TABLE model_new RENAME TO model")
    connection.execute("ALTER TABLE asset_number_new RENAME TO asset_number")

    connection.execute("CREATE INDEX idx_equipment_group_area_id ON equipment_group (area_id)")
    connection.execute(
        "CREATE INDEX idx_equipment_group_equipment_group "
        "ON equipment_group (equipment_group)"
    )
    connection.execute(
        "CREATE INDEX idx_model_equipment_group_id ON model (equipment_group_id)"
    )
    connection.execute("CREATE INDEX idx_model_model ON model (model)")
    connection.execute("CREATE INDEX idx_asset_number_model_id ON asset_number (model_id)")
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number ON asset_number (asset_number)"
    )
    connection.execute("PRAGMA foreign_keys = ON")
    connection.commit()


def print_validation(connection: sqlite3.Connection) -> None:
    checks = [
        ("area rows", "SELECT COUNT(*) FROM area"),
        ("equipment_group rows", "SELECT COUNT(*) FROM equipment_group"),
        ("model rows", "SELECT COUNT(*) FROM model"),
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
            "model orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM model m
            LEFT JOIN equipment_group eg
              ON eg.equipment_group_id = m.equipment_group_id
            WHERE eg.equipment_group_id IS NULL
            """,
        ),
        (
            "asset_number orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM asset_number an
            LEFT JOIN model m
              ON m.model_id = an.model_id
            WHERE an.model_id IS NOT NULL
              AND m.model_id IS NULL
            """,
        ),
        ("asset_number missing model_id", "SELECT COUNT(*) FROM asset_number WHERE model_id IS NULL"),
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
        rebuild_hierarchy(connection)
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
