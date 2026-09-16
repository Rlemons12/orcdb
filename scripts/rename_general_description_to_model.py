"""Rename the general_description hierarchy level to model in BOM.db."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rename general_description table/columns to model/model_id."
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
        f"{db_path.stem}_before_model_rename_{stamp}{db_path.suffix}"
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


def source_table_name(connection: sqlite3.Connection) -> str:
    if table_exists(connection, "model"):
        return "model"
    if table_exists(connection, "general_description"):
        return "general_description"
    raise SystemExit("Missing source table: general_description or model")


def rebuild_model(connection: sqlite3.Connection) -> None:
    source_table = source_table_name(connection)
    source_columns = columns_for(connection, source_table)
    asset_number_columns = columns_for(connection, "asset_number")

    source_id = "model_id" if "model_id" in source_columns else "general_description_id"
    source_text = "model" if "model" in source_columns else "general_description"
    asset_fk = "model_id" if "model_id" in asset_number_columns else "general_description_id"

    required_source = {source_id, "equipment_group_id", source_text}
    missing_source = required_source - source_columns
    if missing_source:
        raise SystemExit(f"{source_table} is missing column(s): {sorted(missing_source)}")

    required_asset = {asset_fk, "asset_number", "asset_description"}
    missing_asset = required_asset - asset_number_columns
    if missing_asset:
        raise SystemExit(f"asset_number is missing column(s): {sorted(missing_asset)}")

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS asset_number_new")
    connection.execute("DROP TABLE IF EXISTS model_new")
    connection.execute(
        """
        CREATE TABLE model_new (
            model_id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_group_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            FOREIGN KEY (equipment_group_id)
                REFERENCES equipment_group (equipment_group_id),
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
            {source_id},
            equipment_group_id,
            {source_text}
        FROM {source_table}
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
        f"""
        INSERT INTO asset_number_new (
            model_id,
            asset_number,
            asset_description
        )
        SELECT
            {asset_fk},
            asset_number,
            asset_description
        FROM asset_number
        """
    )
    connection.execute("DROP TABLE asset_number")
    if source_table == "general_description":
        connection.execute("DROP TABLE general_description")
    else:
        connection.execute("DROP TABLE model")
    connection.execute("ALTER TABLE model_new RENAME TO model")
    connection.execute("ALTER TABLE asset_number_new RENAME TO asset_number")
    connection.execute(
        "CREATE INDEX idx_model_equipment_group_id ON model (equipment_group_id)"
    )
    connection.execute("CREATE INDEX idx_model_model ON model (model)")
    connection.execute(
        "CREATE INDEX idx_asset_number_model_id ON asset_number (model_id)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number ON asset_number (asset_number)"
    )
    connection.execute("PRAGMA foreign_keys = ON")
    connection.commit()


def print_validation(connection: sqlite3.Connection) -> None:
    checks = [
        ("model rows", "SELECT COUNT(*) FROM model"),
        ("asset_number rows", "SELECT COUNT(*) FROM asset_number"),
        (
            "model orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM model m
            LEFT JOIN equipment_group ag
              ON ag.equipment_group_id = m.equipment_group_id
            WHERE ag.equipment_group_id IS NULL
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
        (
            "asset_number missing model_id",
            "SELECT COUNT(*) FROM asset_number WHERE model_id IS NULL",
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
        rebuild_model(connection)
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
