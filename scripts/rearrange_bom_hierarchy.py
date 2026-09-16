"""Rearrange BOM hierarchy to department -> asset group -> description -> asset."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the exact BOM hierarchy: area -> equipment_group -> "
            "model -> asset_number."
        )
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


def make_backup(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(
        f"{db_path.stem}_before_exact_hierarchy_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def columns_for(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


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
        for table_name in (
            "area",
            "equipment_group",
            "model",
            "asset_number",
        )
        if not table_exists(connection, table_name)
    ]
    if missing:
        raise SystemExit(f"Missing required table(s): {missing}")


def first_existing(columns: set[str], choices: tuple[str, ...], table_name: str) -> str:
    for choice in choices:
        if choice in columns:
            return choice
    raise SystemExit(f"{table_name} is missing one of: {choices}")


def rebuild_hierarchy(connection: sqlite3.Connection) -> None:
    require_tables(connection)
    equipment_group_columns = columns_for(connection, "equipment_group")
    model_columns = columns_for(connection, "model")
    asset_number_columns = columns_for(connection, "asset_number")

    equipment_group_pk = first_existing(
        equipment_group_columns,
        ("equipment_group_id", "equipment_group_id"),
        "equipment_group",
    )
    model_group_fk = first_existing(
        model_columns,
        ("equipment_group_id", "equipment_group_id"),
        "model",
    )

    required_equipment_group = {"area_id", "equipment_group"}
    missing_equipment_group = required_equipment_group - equipment_group_columns
    if missing_equipment_group:
        raise SystemExit(
            f"equipment_group is missing required column(s): {sorted(missing_equipment_group)}"
        )

    required_model = {"model_id", "model"}
    missing_model = required_model - model_columns
    if missing_model:
        raise SystemExit(
            "model is missing required column(s): "
            f"{sorted(missing_model)}"
        )

    required_asset_number = {
        "model_id",
        "asset_number",
        "asset_description",
    }
    missing_asset_number = required_asset_number - asset_number_columns
    if missing_asset_number:
        raise SystemExit(
            f"asset_number is missing required column(s): {sorted(missing_asset_number)}"
        )

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS asset_number_new")
    connection.execute("DROP TABLE IF EXISTS model_new")
    connection.execute("DROP TABLE IF EXISTS equipment_group_new")

    connection.execute(
        """
        CREATE TABLE equipment_group_new (
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
        f"""
        INSERT INTO equipment_group_new (
            equipment_group_id,
            area_id,
            equipment_group,
            equipment_group_description
        )
        SELECT
            {equipment_group_pk},
            area_id,
            equipment_group,
            equipment_group_description
        FROM equipment_group
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
    connection.execute("DROP TABLE equipment_group")
    connection.execute("ALTER TABLE equipment_group_new RENAME TO equipment_group")
    connection.execute("ALTER TABLE model_new RENAME TO model")
    connection.execute("ALTER TABLE asset_number_new RENAME TO asset_number")

    connection.execute(
        "CREATE INDEX idx_equipment_group_area_id "
        "ON equipment_group (area_id)"
    )
    connection.execute(
        "CREATE INDEX idx_equipment_group_equipment_group "
        "ON equipment_group (equipment_group)"
    )
    connection.execute(
        "CREATE INDEX idx_model_equipment_group_id "
        "ON model (equipment_group_id)"
    )
    connection.execute(
        "CREATE INDEX idx_model_description "
        "ON model (model)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_model_id "
        "ON asset_number (model_id)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number "
        "ON asset_number (asset_number)"
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
            FROM equipment_group ag
            LEFT JOIN area dc
              ON dc.area_id = ag.area_id
            WHERE dc.area_id IS NULL
            """,
        ),
        (
            "model orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM model gd
            LEFT JOIN equipment_group ag
              ON ag.equipment_group_id = gd.equipment_group_id
            WHERE ag.equipment_group_id IS NULL
            """,
        ),
        (
            "asset_number orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM asset_number an
            LEFT JOIN model gd
              ON gd.model_id = an.model_id
            WHERE an.model_id IS NOT NULL
              AND gd.model_id IS NULL
            """,
        ),
        (
            "asset_number missing model_id",
            """
            SELECT COUNT(*)
            FROM asset_number
            WHERE model_id IS NULL
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
        rebuild_hierarchy(connection)
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
