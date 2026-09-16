"""Remove duplicated model text from asset_number."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild asset_number without the duplicated model column."
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
        f"{db_path.stem}_before_remove_asset_model_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def columns_for(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def rebuild_asset_number(connection: sqlite3.Connection) -> None:
    required = {
        "model_id",
        "asset_number",
        "asset_description",
    }
    missing = required - columns_for(connection, "asset_number")
    if missing:
        raise SystemExit(f"asset_number is missing required column(s): {sorted(missing)}")

    if "model" not in columns_for(connection, "asset_number"):
        print("asset_number.model is already removed")
        return

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS asset_number_new")
    connection.execute(
        """
        CREATE TABLE asset_number_new (
            model_id INTEGER,
            asset_number TEXT NOT NULL,
            asset_description TEXT,
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
    connection.execute("ALTER TABLE asset_number_new RENAME TO asset_number")
    connection.execute(
        "CREATE INDEX idx_asset_number_model_id ON asset_number (model_id)"
    )
    connection.execute(
        "CREATE INDEX idx_asset_number_asset_number ON asset_number (asset_number)"
    )
    connection.execute("PRAGMA foreign_keys = ON")
    connection.commit()


def print_validation(connection: sqlite3.Connection) -> None:
    print("asset_number columns:")
    for row in connection.execute("PRAGMA table_info(asset_number)"):
        print(f"- {row[1]}")
    print(
        "asset_number rows:",
        connection.execute("SELECT COUNT(*) FROM asset_number").fetchone()[0],
    )
    print(
        "model rows:",
        connection.execute("SELECT COUNT(*) FROM model").fetchone()[0],
    )
    print(
        "asset_number model orphan foreign keys:",
        connection.execute(
            """
            SELECT COUNT(*)
            FROM asset_number an
            LEFT JOIN model gd
              ON gd.model_id = an.model_id
            WHERE an.model_id IS NOT NULL
              AND gd.model_id IS NULL
            """
        ).fetchone()[0],
    )


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    backup_path = None
    if not args.no_backup:
        backup_path = make_backup(db_path)

    with sqlite3.connect(db_path) as connection:
        rebuild_asset_number(connection)
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
