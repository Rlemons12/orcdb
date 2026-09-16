"""Add drawing.position_id and populate it from the position mapper."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Link drawing rows to position using area, equipment_group, model, "
            "and asset_number."
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
        f"{db_path.stem}_before_drawing_position_link_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def key(value: object) -> str | None:
    text = clean(value)
    return text.upper() if text else None


def asset_base(value: object) -> str | None:
    text = key(value)
    if not text:
        return None
    return text.split("-", 1)[0] if "-" in text else text


def table_columns(connection: sqlite3.Connection, table_name: str) -> list[str]:
    return [row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")]


def require_schema(connection: sqlite3.Connection) -> None:
    required_drawing = {"area", "equipment_group", "model", "asset_number"}
    drawing_columns = set(table_columns(connection, "drawing"))
    missing_drawing = required_drawing - drawing_columns
    if missing_drawing:
        raise SystemExit(f"drawing is missing column(s): {sorted(missing_drawing)}")

    required_position = {"id", "area_id", "equipment_group_id", "model_id", "asset_number"}
    position_columns = set(table_columns(connection, "position"))
    missing_position = required_position - position_columns
    if missing_position:
        raise SystemExit(f"position is missing column(s): {sorted(missing_position)}")


def load_position_maps(
    connection: sqlite3.Connection,
) -> tuple[dict[tuple[str, str, str, str], int], dict[tuple[str, str, str, str], int]]:
    exact_candidates: defaultdict[tuple[str, str, str, str], list[int]] = defaultdict(list)
    base_candidates: defaultdict[tuple[str, str, str, str], list[int]] = defaultdict(list)

    rows = connection.execute(
        """
        SELECT
            p.id,
            a.area,
            eg.equipment_group,
            m.model,
            an.asset_number
        FROM position p
        JOIN asset_number an
          ON an.asset_number_id = p.asset_number_id
        JOIN area a
          ON a.area_id = p.area_id
        JOIN equipment_group eg
          ON eg.equipment_group_id = p.equipment_group_id
        JOIN model m
          ON m.model_id = p.model_id
        WHERE p.asset_number IS NOT NULL
          AND LENGTH(TRIM(p.asset_number)) > 0
        """
    ).fetchall()

    for position_id, area, equipment_group, model, asset_number in rows:
        area_key = key(area)
        equipment_key = key(equipment_group)
        model_key = key(model)
        asset_key = key(asset_number)
        base_key = asset_base(asset_number)
        if area_key and equipment_key and model_key and asset_key:
            exact_candidates[(area_key, equipment_key, model_key, asset_key)].append(position_id)
        if area_key and equipment_key and model_key and base_key:
            base_candidates[(area_key, equipment_key, model_key, base_key)].append(position_id)

    exact = {candidate_key: sorted(ids)[0] for candidate_key, ids in exact_candidates.items()}
    base = {candidate_key: sorted(ids)[0] for candidate_key, ids in base_candidates.items()}
    return exact, base


def matching_position_id(
    row: dict[str, object],
    exact_positions: dict[tuple[str, str, str, str], int],
    base_positions: dict[tuple[str, str, str, str], int],
) -> tuple[int | None, str | None]:
    area_key = key(row.get("area"))
    equipment_key = key(row.get("equipment_group"))
    model_key = key(row.get("model"))
    asset_key = key(row.get("asset_number"))
    if not area_key or not equipment_key or not model_key or not asset_key:
        return None, None

    exact_key = (area_key, equipment_key, model_key, asset_key)
    if exact_key in exact_positions:
        return exact_positions[exact_key], "exact"

    base_key = (area_key, equipment_key, model_key, asset_base(asset_key))
    if base_key in base_positions:
        return base_positions[base_key], "base"

    return None, None


def rebuild_drawing(connection: sqlite3.Connection) -> dict[str, int]:
    require_schema(connection)
    exact_positions, base_positions = load_position_maps(connection)
    source_columns = [
        column for column in table_columns(connection, "drawing") if column != "position_id"
    ]
    select_columns = ", ".join(source_columns)
    rows = connection.execute(
        f"SELECT rowid, {select_columns} FROM drawing ORDER BY rowid"
    ).fetchall()

    stats = {
        "drawing_rows": len(rows),
        "linked_rows": 0,
        "exact_link_rows": 0,
        "base_link_rows": 0,
        "unlinked_rows": 0,
    }
    output_rows = []
    for row in rows:
        rowid = row[0]
        values = dict(zip(source_columns, row[1:]))
        position_id, match_type = matching_position_id(values, exact_positions, base_positions)
        if position_id is None:
            stats["unlinked_rows"] += 1
        else:
            stats["linked_rows"] += 1
            stats[f"{match_type}_link_rows"] += 1
        output_rows.append((position_id, *[values[column] for column in source_columns]))

    connection.execute("PRAGMA foreign_keys = OFF")
    connection.execute("DROP TABLE IF EXISTS drawing_new")
    column_sql = ",\n            ".join(f"{column} TEXT" for column in source_columns)
    connection.execute(
        f"""
        CREATE TABLE drawing_new (
            position_id INTEGER,
            {column_sql},
            FOREIGN KEY (position_id)
                REFERENCES position (id)
        )
        """
    )
    insert_columns = ", ".join(["position_id", *source_columns])
    placeholders = ", ".join("?" for _ in ["position_id", *source_columns])
    connection.executemany(
        f"INSERT INTO drawing_new ({insert_columns}) VALUES ({placeholders})",
        output_rows,
    )
    connection.execute("DROP TABLE drawing")
    connection.execute("ALTER TABLE drawing_new RENAME TO drawing")
    connection.execute("CREATE INDEX idx_drawing_position_id ON drawing (position_id)")
    for column in ("area", "equipment_group", "model", "asset_number", "drawing_number"):
        if column in source_columns:
            connection.execute(f"CREATE INDEX idx_drawing_{column} ON drawing ({column})")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.commit()
    return stats


def print_validation(connection: sqlite3.Connection, stats: dict[str, int]) -> None:
    for label, value in stats.items():
        print(f"{label}: {value}")
    checks = [
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
        ("drawing rows with position_id", "SELECT COUNT(*) FROM drawing WHERE position_id IS NOT NULL"),
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
        stats = rebuild_drawing(connection)
        print_validation(connection, stats)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
