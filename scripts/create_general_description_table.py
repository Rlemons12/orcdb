"""Normalize asset_number.model under each asset group."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create equipment_group-scoped model rows and link "
            "asset_number rows to them."
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
        f"{db_path.stem}_before_model_table_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def columns_for(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def require_asset_number_columns(connection: sqlite3.Connection) -> None:
    required = {
        "equipment_group_id",
        "asset_number",
        "asset_description",
        "model",
    }
    existing = columns_for(connection, "asset_number")
    missing = required - existing
    if missing:
        raise SystemExit(f"asset_number is missing required column(s): {sorted(missing)}")


def rebuild_model(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")
    require_asset_number_columns(connection)

    connection.execute("DROP TABLE IF EXISTS model")
    connection.execute(
        """
        CREATE TABLE model (
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
        """
        INSERT INTO model (
            equipment_group_id,
            model
        )
        SELECT
            equipment_group_id,
            model
        FROM asset_number
        WHERE NULLIF(TRIM(model), '') IS NOT NULL
        GROUP BY
            equipment_group_id,
            model
        ORDER BY
            equipment_group_id,
            model
        """
    )

    current_columns = columns_for(connection, "asset_number")
    if "model_id" not in current_columns:
        connection.execute("ALTER TABLE asset_number ADD COLUMN model_id INTEGER")

    connection.execute(
        """
        UPDATE asset_number
        SET model_id = (
            SELECT gd.model_id
            FROM model gd
            WHERE gd.equipment_group_id = asset_number.equipment_group_id
              AND gd.model = asset_number.model
        )
        WHERE NULLIF(TRIM(model), '') IS NOT NULL
        """
    )

    # SQLite cannot add a foreign key constraint to an existing table. Rebuild the
    # table so asset_number.model_id is formally constrained.
    connection.execute("DROP TABLE IF EXISTS asset_number_new")
    connection.execute(
        """
        CREATE TABLE asset_number_new (
            model_id INTEGER,
            asset_number TEXT NOT NULL,
            asset_description TEXT,
            model TEXT,
            FOREIGN KEY (model_id)
                REFERENCES model (model_id),
            UNIQUE (model_id, asset_number)
        )
        """
    )
    connection.execute(
        """
        INSERT INTO asset_number_new (
            model_id,
            asset_number,
            asset_description,
            model
        )
        SELECT
            model_id,
            asset_number,
            asset_description,
            model
        FROM asset_number
        """
    )
    connection.execute("DROP TABLE asset_number")
    connection.execute("ALTER TABLE asset_number_new RENAME TO asset_number")
    connection.execute(
        "CREATE INDEX idx_asset_number_model_id ON asset_number (model_id)"
    )
    connection.execute(
        "CREATE INDEX idx_model_equipment_group_id "
        "ON model (equipment_group_id)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number ON asset_number (asset_number)"
    )
    connection.execute(
        "CREATE INDEX idx_model_description ON model (model)"
    )
    connection.execute("PRAGMA foreign_keys = ON")
    connection.commit()


def print_validation(connection: sqlite3.Connection) -> None:
    counts = [
        ("model rows", "SELECT COUNT(*) FROM model"),
        ("asset_number rows", "SELECT COUNT(*) FROM asset_number"),
        (
            "asset_number missing model_id",
            """
            SELECT COUNT(*)
            FROM asset_number
            WHERE NULLIF(TRIM(model), '') IS NOT NULL
              AND model_id IS NULL
            """,
        ),
        (
            "asset_number model orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM asset_number an
            LEFT JOIN model gd
              ON gd.model_id = an.model_id
            WHERE an.model_id IS NOT NULL
              AND gd.model_id IS NULL
            """,
        ),
    ]
    for label, query in counts:
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
