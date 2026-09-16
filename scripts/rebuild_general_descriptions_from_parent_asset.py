"""Rebuild model using parent -00 assets for section asset numbers."""

from __future__ import annotations

import argparse
import re
import shutil
import sqlite3
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from create_general_asset_description import generalize_description


SECTION_ASSET_RE = re.compile(r"^(?P<base>.+)-(?P<section>\d{2})$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Rebuild model so section assets like ABM50400-51 "
            "use the matching ABM50400-00 parent description."
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
        f"{db_path.stem}_before_parent_model_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def parent_base(asset_number: str | None) -> tuple[str, str] | None:
    if not asset_number:
        return None
    match = SECTION_ASSET_RE.match(asset_number.strip().upper())
    if not match:
        return None
    return match.group("base"), match.group("section")


def select_parent_descriptions(rows: list[sqlite3.Row]) -> dict[str, str]:
    descriptions_by_base: defaultdict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        parsed = parent_base(row["asset_number"])
        description = (row["asset_description"] or "").strip()
        if not parsed or not description:
            continue
        base, section = parsed
        if section == "00":
            descriptions_by_base[base][description] += 1

    selected = {}
    for base, counter in descriptions_by_base.items():
        selected[base] = sorted(counter.items(), key=lambda item: (-item[1], item[0]))[0][0]
    return selected


def derive_descriptions(rows: list[sqlite3.Row]) -> tuple[dict[int, tuple[int, str]], int]:
    parent_descriptions = select_parent_descriptions(rows)
    derived: dict[int, tuple[int, str]] = {}
    parent_applied_count = 0

    for row in rows:
        source_description = row["asset_description"]
        parsed = parent_base(row["asset_number"])
        if parsed:
            base, section = parsed
            if section != "00" and base in parent_descriptions:
                source_description = parent_descriptions[base]
                parent_applied_count += 1

        model = generalize_description(source_description)
        if model and row["equipment_group_id"] is not None:
            derived[row["asset_rowid"]] = (
                row["equipment_group_id"],
                model,
            )

    return derived, parent_applied_count


def rebuild_lookup(
    connection: sqlite3.Connection,
    derived: dict[int, tuple[int, str]],
) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")
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

    descriptions = sorted(set(derived.values()))
    connection.executemany(
        """
        INSERT INTO model (
            equipment_group_id,
            model
        )
        VALUES (?, ?)
        """,
        descriptions,
    )

    connection.execute("DROP TABLE IF EXISTS temp_asset_model")
    connection.execute(
        """
        CREATE TEMP TABLE temp_asset_model (
            asset_rowid INTEGER PRIMARY KEY,
            equipment_group_id INTEGER NOT NULL,
            model TEXT NOT NULL
        )
        """
    )
    connection.executemany(
        """
        INSERT INTO temp_asset_model (
            asset_rowid,
            equipment_group_id,
            model
        )
        VALUES (?, ?, ?)
        """,
        [
            (asset_rowid, equipment_group_id, model)
            for asset_rowid, (
                equipment_group_id,
                model,
            ) in sorted(derived.items())
        ],
    )
    connection.execute("UPDATE asset_number SET model_id = NULL")
    connection.execute(
        """
        UPDATE asset_number
        SET model_id = (
            SELECT gd.model_id
            FROM temp_asset_model tagd
            JOIN model gd
              ON gd.equipment_group_id = tagd.equipment_group_id
             AND gd.model = tagd.model
            WHERE tagd.asset_rowid = asset_number.rowid
        )
        WHERE rowid IN (
            SELECT asset_rowid
            FROM temp_asset_model
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_model_description "
        "ON model (model)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_model_equipment_group_id "
        "ON model (equipment_group_id)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_asset_number_model_id "
        "ON asset_number (model_id)"
    )
    connection.execute("PRAGMA foreign_keys = ON")
    connection.commit()


def print_validation(connection: sqlite3.Connection, parent_applied_count: int) -> None:
    print(f"section assets assigned from -00 parent: {parent_applied_count}")
    print(
        "model rows:",
        connection.execute("SELECT COUNT(*) FROM model").fetchone()[0],
    )
    print(
        "asset_number rows:",
        connection.execute("SELECT COUNT(*) FROM asset_number").fetchone()[0],
    )
    print(
        "asset_number missing model_id:",
        connection.execute(
            """
            SELECT COUNT(*)
            FROM asset_number
            WHERE asset_description IS NOT NULL
              AND TRIM(asset_description) <> ''
              AND model_id IS NULL
            """
        ).fetchone()[0],
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
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT
                asset_number.rowid AS asset_rowid,
                gd.equipment_group_id AS equipment_group_id,
                asset_number,
                asset_description
            FROM asset_number
            LEFT JOIN model gd
              ON gd.model_id = asset_number.model_id
            """
        ).fetchall()
        derived, parent_applied_count = derive_descriptions(rows)
        rebuild_lookup(connection, derived)
        print_validation(connection, parent_applied_count)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
