"""Create a derived model field from asset_description."""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


ASSET_TAG_RE = re.compile(r"\b[A-Z]{2,}[-']?[A-Z0-9']*\d+[A-Z0-9'-]*\b")
UNIT_MARKER_WORDS = {
    "GAL",
    "HP",
    "INCH",
    "ISO",
    "KW",
    "KVA",
    "LB",
    "ML",
    "PSI",
    "RPM",
    "VAC",
    "VDC",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate asset_number.model from asset_description."
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
        f"{db_path.stem}_before_model_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def generalize_description(description: str | None) -> str | None:
    if description is None:
        return None

    value = description.strip().upper()
    if not value:
        return None

    value = re.sub(r"\bLIFE\s+CARE\b", "LIFECARE", value)

    value = re.sub(r"\([^)]*\)", " ", value)
    value = re.sub(r"\bNITROGEN\s+FILTER\s+TANK\s+\d+\b", "NITROGEN FILTERS", value)
    value = re.sub(r"\bON\s+[A-Z]{2,}\d+[A-Z0-9-]*\b", " ", value)
    value = re.sub(r"#\s*\d+(?:\s*-\s*\d+)?", " ", value)
    value = re.sub(r"\b\d+\s*-\s*\d+\b", " ", value)

    value = value.replace("&", " AND ")
    value = value.replace("/", " / ")
    value = value.replace("-", " ")
    value = value.replace("_", " ")
    value = value.replace('"', " ")

    value = re.sub(r"\bLINE\s+[A-Z]\b", "LINE", value)
    value = re.sub(r"\bSET\s+[A-Z]\b", "SET", value)
    value = re.sub(r"\bBAY\s+\d+\b", "BAY", value)
    value = re.sub(r"\bSTATION\s+[A-Z]\b", "STATION", value)
    value = re.sub(r"\bAUTO\s+FILLER\s+\d+\b", "AUTO FILLER", value)
    value = re.sub(r"\b(?:ROUND\s+ROCK|RR)\b", " ", value)
    value = re.sub(r"\b(?:NORTH|SOUTH|EAST|WEST)\s+WALL\b", " ", value)
    value = re.sub(r"\b(?:NORTH|SOUTH|EAST|WEST)\b$", " ", value)
    value = re.sub(r"\b(?:AREA|ROOM|RM|WH)\b$", " ", value)
    value = re.sub(r"\b\d+\s+\d+\b$", " ", value)
    value = re.sub(r"\b\d{2,}\b$", " ", value)
    value = re.sub(r"\b[ABCDEF]\b$", " ", value)
    value = ASSET_TAG_RE.sub(" ", value)

    value = re.sub(r"\s*,\s*", ", ", value)
    value = re.sub(r"\s+", " ", value).strip(" ,.-")
    value = remove_trailing_station_marker(value)

    return value or description.strip().upper()


def remove_trailing_station_marker(value: str) -> str:
    """Remove final station tokens like 1, 2, 3, A, or B without dropping units."""
    tokens = value.split()
    if len(tokens) < 2:
        return value

    marker = tokens[-1].strip(" ,.-")
    previous = tokens[-2].strip(" ,.-")
    if previous in UNIT_MARKER_WORDS:
        return value

    if re.fullmatch(r"#?\d{1,3}|[A-Z]", marker):
        return " ".join(tokens[:-1]).strip(" ,.-")

    return value


def register_functions(connection: sqlite3.Connection) -> None:
    connection.create_function("generalize_description", 1, generalize_description)


def ensure_column(connection: sqlite3.Connection) -> None:
    columns = table_columns(connection, "asset_number")
    if "model" not in columns:
        connection.execute("ALTER TABLE asset_number ADD COLUMN model TEXT")


def update_asset_number(connection: sqlite3.Connection) -> int:
    ensure_column(connection)
    connection.execute(
        """
        UPDATE asset_number
        SET model = generalize_description(asset_description)
        """
    )
    return connection.execute("SELECT changes()").fetchone()[0]


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    backup_path = None
    if not args.no_backup:
        backup_path = make_backup(db_path)

    with sqlite3.connect(db_path) as connection:
        register_functions(connection)
        updated = update_asset_number(connection)
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_asset_number_model "
            "ON asset_number (model)"
        )
        unique_general = connection.execute(
            """
            SELECT COUNT(DISTINCT model)
            FROM asset_number
            WHERE model IS NOT NULL
              AND TRIM(model) <> ''
            """
        ).fetchone()[0]
        connection.commit()

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"asset_number rows updated: {updated}")
    print(f"unique models: {unique_general}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
