"""Backfill drawing hierarchy columns from normalized asset hierarchy."""

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
            "Populate drawing.area, drawing.equipment_group, and drawing.model "
            "from asset_number -> model -> equipment_group -> area."
        )
    )
    parser.add_argument("--db", default="data/BOM.db", help="SQLite database path.")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create a timestamped database backup before updating.",
    )
    parser.add_argument(
        "--allow-ambiguous",
        action="store_true",
        help=(
            "When an asset number has multiple hierarchy matches, overwrite with "
            "the first match sorted by area, equipment_group, and model."
        ),
    )
    return parser.parse_args()


def make_backup(db_path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.with_name(
        f"{db_path.stem}_before_drawing_hierarchy_backfill_{stamp}{db_path.suffix}"
    )
    shutil.copy2(db_path, backup_path)
    return backup_path


def clean(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def match_key(value: object) -> str | None:
    text = clean(value)
    return text.upper() if text else None


def base_asset_number(asset_number: object) -> str | None:
    text = match_key(asset_number)
    if not text:
        return None
    if "-" in text:
        return text.split("-", 1)[0]
    return text


def table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}


def require_schema(connection: sqlite3.Connection) -> None:
    required_drawing = {"area", "equipment_group", "model", "asset_number"}
    missing_drawing = required_drawing - table_columns(connection, "drawing")
    if missing_drawing:
        raise SystemExit(f"drawing is missing column(s): {sorted(missing_drawing)}")

    required_asset_number = {"model_id", "asset_number"}
    missing_asset_number = required_asset_number - table_columns(connection, "asset_number")
    if missing_asset_number:
        raise SystemExit(
            f"asset_number is missing column(s): {sorted(missing_asset_number)}"
        )


def load_hierarchy(connection: sqlite3.Connection) -> tuple[dict[str, list[dict]], dict[str, list[dict]]]:
    rows = connection.execute(
        """
        SELECT
            an.asset_number,
            m.model,
            eg.equipment_group,
            a.area
        FROM asset_number an
        JOIN model m
          ON m.model_id = an.model_id
        JOIN equipment_group eg
          ON eg.equipment_group_id = m.equipment_group_id
        JOIN area a
          ON a.area_id = eg.area_id
        WHERE an.asset_number IS NOT NULL
          AND LENGTH(TRIM(an.asset_number)) > 0
        """
    ).fetchall()

    by_exact: defaultdict[str, list[dict]] = defaultdict(list)
    by_base: defaultdict[str, list[dict]] = defaultdict(list)
    for asset_number, model, equipment_group, area in rows:
        candidate = {
            "asset_number": clean(asset_number),
            "model": clean(model),
            "equipment_group": clean(equipment_group),
            "area": clean(area),
        }
        exact_key = match_key(asset_number)
        base_key = base_asset_number(asset_number)
        if exact_key:
            by_exact[exact_key].append(candidate)
        if base_key:
            by_base[base_key].append(candidate)

    return dict(by_exact), dict(by_base)


def values_match(left: object, right: object) -> bool:
    left_key = match_key(left)
    right_key = match_key(right)
    return left_key is not None and left_key == right_key


def choose_candidate(
    candidates: list[dict],
    existing_area: object,
    existing_equipment_group: object,
    existing_model: object,
    allow_ambiguous: bool,
) -> dict | None:
    unique_candidates = {
        (
            candidate["area"],
            candidate["equipment_group"],
            candidate["model"],
        ): candidate
        for candidate in candidates
    }
    remaining = list(unique_candidates.values())
    if len(remaining) == 1:
        return remaining[0]

    for column_name, existing_value in (
        ("area", existing_area),
        ("equipment_group", existing_equipment_group),
        ("model", existing_model),
    ):
        if match_key(existing_value) is None:
            continue
        filtered = [
            candidate
            for candidate in remaining
            if values_match(candidate[column_name], existing_value)
        ]
        if len(filtered) == 1:
            return filtered[0]
        if filtered:
            remaining = filtered

    if len(remaining) == 1:
        return remaining[0]
    if allow_ambiguous:
        return sorted(
            remaining,
            key=lambda candidate: (
                candidate["area"] or "",
                candidate["equipment_group"] or "",
                candidate["model"] or "",
            ),
        )[0]
    return None


def backfill(connection: sqlite3.Connection, allow_ambiguous: bool) -> dict[str, int]:
    require_schema(connection)
    by_exact, by_base = load_hierarchy(connection)

    drawing_rows = connection.execute(
        """
        SELECT
            rowid,
            asset_number,
            area,
            equipment_group,
            model
        FROM drawing
        WHERE asset_number IS NOT NULL
          AND LENGTH(TRIM(asset_number)) > 0
        """
    ).fetchall()

    updates = []
    stats = {
        "drawing_rows_with_asset_number": len(drawing_rows),
        "updated_rows": 0,
        "exact_match_rows": 0,
        "base_match_rows": 0,
        "unmatched_rows": 0,
        "ambiguous_rows": 0,
    }

    for rowid, asset_number, area, equipment_group, model in drawing_rows:
        key = match_key(asset_number)
        candidates = by_exact.get(key or "", [])
        match_type = "exact"
        if not candidates:
            candidates = by_base.get(base_asset_number(asset_number) or "", [])
            match_type = "base"

        if not candidates:
            stats["unmatched_rows"] += 1
            continue

        candidate = choose_candidate(
            candidates,
            area,
            equipment_group,
            model,
            allow_ambiguous,
        )
        if candidate is None:
            stats["ambiguous_rows"] += 1
            continue

        updates.append(
            (
                candidate["area"],
                candidate["equipment_group"],
                candidate["model"],
                rowid,
            )
        )
        stats[f"{match_type}_match_rows"] += 1

    connection.executemany(
        """
        UPDATE drawing
        SET
            area = ?,
            equipment_group = ?,
            model = ?
        WHERE rowid = ?
        """,
        updates,
    )
    connection.commit()
    stats["updated_rows"] = len(updates)
    stats["ambiguous_mode"] = int(allow_ambiguous)
    return stats


def print_validation(connection: sqlite3.Connection, stats: dict[str, int]) -> None:
    for label, value in stats.items():
        print(f"{label}: {value}")
    print(
        "drawing rows with full hierarchy:",
        connection.execute(
            """
            SELECT COUNT(*)
            FROM drawing
            WHERE area IS NOT NULL
              AND equipment_group IS NOT NULL
              AND model IS NOT NULL
            """
        ).fetchone()[0],
    )
    print(
        "drawing rows matching full hierarchy now:",
        connection.execute(
            """
            SELECT COUNT(*)
            FROM drawing d
            WHERE EXISTS (
                SELECT 1
                FROM asset_number an
                JOIN model m
                  ON m.model_id = an.model_id
                JOIN equipment_group eg
                  ON eg.equipment_group_id = m.equipment_group_id
                JOIN area a
                  ON a.area_id = eg.area_id
                WHERE (
                    UPPER(TRIM(an.asset_number)) = UPPER(TRIM(d.asset_number))
                    OR (
                        INSTR(an.asset_number, '-') > 0
                        AND UPPER(SUBSTR(an.asset_number, 1, INSTR(an.asset_number, '-') - 1))
                            = UPPER(TRIM(d.asset_number))
                    )
                )
                  AND a.area = d.area
                  AND eg.equipment_group = d.equipment_group
                  AND m.model = d.model
            )
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
        stats = backfill(connection, args.allow_ambiguous)
        print_validation(connection, stats)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
