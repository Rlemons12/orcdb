"""Build an EMTAC-style asset hierarchy database from BOM data."""

from __future__ import annotations

import argparse
import csv
import re
import sqlite3
from pathlib import Path

from create_general_asset_description import generalize_description


DEFAULT_SOURCE_DB = "data/BOM.db"
DEFAULT_TARGET_DB = "data/emtac.db"
DEFAULT_UNKNOWN_AREA = "UNKNOWN"
DEFAULT_ORG_CODE = "XAU"

FILLER_SUFFIX_RE = re.compile(
    r"\bFOR\s+(?:AUTOMATIC\s+|MANUAL\s+)?FILLERS?(?:\s+\d+(?:\s*-\s*\d+)?)?\b"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build area -> equipment_group -> model -> asset_number and "
            "model -> location hierarchy tables from boms_for_department."
        )
    )
    parser.add_argument("--source-db", default=DEFAULT_SOURCE_DB)
    parser.add_argument(
        "--source-csv",
        help=(
            "Optional Oracle asset hierarchy CSV. When supplied, this is used "
            "instead of boms_for_department in --source-db."
        ),
    )
    parser.add_argument(
        "--org-code",
        default=DEFAULT_ORG_CODE,
        help=(
            "Organization code to keep when --source-csv includes "
            "ORGANIZATION_CODE. Use an empty value to disable this filter."
        ),
    )
    parser.add_argument(
        "--area-codes",
        help=(
            "Optional comma-separated DEPARTMENT_CODE values to keep when "
            "--source-csv is used."
        ),
    )
    parser.add_argument("--target-db", default=DEFAULT_TARGET_DB)
    return parser.parse_args()


def normalize_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if not normalized:
        return None
    normalized = normalized.replace("&", " AND ")
    normalized = normalized.replace("_", " ")
    normalized = normalized.replace("-", " ")
    normalized = normalized.replace("/", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip(" ,.-")
    return normalized or None


def normalize_asset_number(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if not normalized:
        return None
    if normalized.startswith("AU-"):
        normalized = normalized[3:]
    return normalized


def derive_model(asset_description: str | None) -> str | None:
    model = generalize_description(asset_description)
    model = normalize_text(model)
    if not model:
        return None

    model = FILLER_SUFFIX_RE.sub(" ", model)
    model = re.sub(r"\bLINE\s+\d+\s+(CASE\s+FORMER)\b", r"\1", model)
    model = re.sub(r"\s+", " ", model).strip(" ,.-")
    return model or None


def require_source_table(connection: sqlite3.Connection) -> None:
    exists = connection.execute(
        """
        SELECT 1
        FROM sqlite_master
        WHERE type = 'table'
          AND name = 'boms_for_department'
        """
    ).fetchone()
    if not exists:
        raise SystemExit("Missing source table: boms_for_department")


def create_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = OFF")
    for table in ("location", "asset_number", "model", "equipment_group", "area"):
        connection.execute(f"DROP TABLE IF EXISTS {table}")

    connection.execute(
        """
        CREATE TABLE area (
            area_id INTEGER PRIMARY KEY,
            area TEXT NOT NULL UNIQUE
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE equipment_group (
            equipment_group_id INTEGER PRIMARY KEY,
            area_id INTEGER NOT NULL,
            equipment_group TEXT NOT NULL,
            UNIQUE (area_id, equipment_group),
            FOREIGN KEY (area_id)
                REFERENCES area (area_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE model (
            model_id INTEGER PRIMARY KEY,
            equipment_group_id INTEGER NOT NULL,
            model TEXT NOT NULL,
            UNIQUE (equipment_group_id, model),
            FOREIGN KEY (equipment_group_id)
                REFERENCES equipment_group (equipment_group_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE asset_number (
            asset_number_id INTEGER PRIMARY KEY,
            model_id INTEGER NOT NULL,
            asset_number TEXT NOT NULL,
            asset_description TEXT,
            UNIQUE (model_id, asset_number),
            FOREIGN KEY (model_id)
                REFERENCES model (model_id)
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE location (
            location_id INTEGER PRIMARY KEY,
            model_id INTEGER NOT NULL,
            location TEXT NOT NULL,
            location_description TEXT,
            UNIQUE (model_id, location),
            FOREIGN KEY (model_id)
                REFERENCES model (model_id)
        )
        """
    )
    connection.execute("PRAGMA foreign_keys = ON")


def populate_target(
    target: sqlite3.Connection,
    assets: set[tuple[str, str, str, str, str | None]],
) -> dict[str, int]:
    areas = sorted({area for area, _, _, _, _ in assets})
    equipment_groups = sorted({(area, group) for area, group, _, _, _ in assets})

    target.executemany("INSERT INTO area (area) VALUES (?)", [(area,) for area in areas])
    area_ids = {
        area: area_id
        for area_id, area in target.execute("SELECT area_id, area FROM area")
    }

    equipment_group_rows = [
        (area_ids[area], group) for area, group in equipment_groups
    ]
    target.executemany(
        "INSERT INTO equipment_group (area_id, equipment_group) VALUES (?, ?)",
        equipment_group_rows,
    )
    equipment_group_ids = {
        (area, group): equipment_group_id
        for equipment_group_id, area, group in target.execute(
            """
            SELECT
                equipment_group.equipment_group_id,
                area.area,
                equipment_group.equipment_group
            FROM equipment_group
            JOIN area
              ON area.area_id = equipment_group.area_id
            """
        )
    }

    models = sorted({
        (equipment_group_ids[(area, group)], model)
        for area, group, model, _, _ in assets
    })
    target.executemany(
        "INSERT INTO model (equipment_group_id, model) VALUES (?, ?)",
        models,
    )
    model_ids = {
        (equipment_group_id, model): model_id
        for model_id, equipment_group_id, model in target.execute(
            "SELECT model_id, equipment_group_id, model FROM model"
        )
    }

    asset_by_key: dict[tuple[int, str], str | None] = {}
    for area, group, model, asset, description in sorted(assets):
        equipment_group_id = equipment_group_ids[(area, group)]
        key = (model_ids[(equipment_group_id, model)], asset)
        if key not in asset_by_key or asset_by_key[key] is None:
            asset_by_key[key] = description
    asset_rows = [
        (model_id, asset, description)
        for (model_id, asset), description in sorted(asset_by_key.items())
    ]
    target.executemany(
        """
        INSERT INTO asset_number (
            model_id,
            asset_number,
            asset_description
        )
        VALUES (?, ?, ?)
        """,
        asset_rows,
    )

    target.execute("CREATE INDEX idx_equipment_group_area_id ON equipment_group (area_id)")
    target.execute("CREATE INDEX idx_equipment_group_group ON equipment_group (equipment_group)")
    target.execute("CREATE INDEX idx_model_equipment_group_id ON model (equipment_group_id)")
    target.execute("CREATE INDEX idx_model_model ON model (model)")
    target.execute("CREATE INDEX idx_asset_number_asset ON asset_number (asset_number)")
    target.execute("CREATE INDEX idx_asset_number_model_id ON asset_number (model_id)")
    target.commit()

    return {
        "area": len(areas),
        "equipment_group": len(equipment_groups),
        "model": len(models),
        "asset_number": len(asset_rows),
        "location": 0,
    }


def build_hierarchy(source_db: Path, target_db: Path) -> dict[str, int]:
    if not source_db.exists():
        raise SystemExit(f"Source database does not exist: {source_db}")
    target_db.parent.mkdir(parents=True, exist_ok=True)

    source = sqlite3.connect(source_db)
    target = sqlite3.connect(target_db)
    try:
        require_source_table(source)
        create_schema(target)

        rows = source.execute(
            """
            SELECT
                TRIM(department_code) AS area,
                TRIM(asset_group_description) AS equipment_group,
                CASE
                    WHEN TRIM(asset_number) LIKE 'AU-%'
                        THEN SUBSTR(TRIM(asset_number), 4)
                    ELSE TRIM(asset_number)
                END AS asset_number,
                MAX(NULLIF(TRIM(asset_description), '')) AS asset_description
            FROM boms_for_department
            WHERE NULLIF(TRIM(department_code), '') IS NOT NULL
              AND NULLIF(TRIM(asset_group_description), '') IS NOT NULL
              AND NULLIF(TRIM(asset_number), '') IS NOT NULL
            GROUP BY
                TRIM(department_code),
                TRIM(asset_group_description),
                CASE
                    WHEN TRIM(asset_number) LIKE 'AU-%'
                        THEN SUBSTR(TRIM(asset_number), 4)
                    ELSE TRIM(asset_number)
                END
            ORDER BY
                area,
                equipment_group,
                asset_number
            """
        ).fetchall()

        assets: set[tuple[str, str, str, str, str | None]] = set()
        for area_raw, group_raw, asset_raw, description in rows:
            area = normalize_text(area_raw)
            equipment_group = normalize_text(group_raw)
            asset = normalize_asset_number(asset_raw)
            model = derive_model(description)
            if not area or not equipment_group or not asset or not model:
                continue
            assets.add((area, equipment_group, model, asset, description))

        return populate_target(target, assets)
    finally:
        source.close()
        target.close()


def build_hierarchy_from_csv(
    source_csv: Path,
    target_db: Path,
    org_code: str | None = DEFAULT_ORG_CODE,
    area_codes: set[str] | None = None,
) -> dict[str, int]:
    if not source_csv.exists():
        raise SystemExit(f"Source CSV does not exist: {source_csv}")
    target_db.parent.mkdir(parents=True, exist_ok=True)

    target = sqlite3.connect(target_db)
    try:
        create_schema(target)
        with source_csv.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            required = {
                "DEPARTMENT_CODE",
                "ASSET_GROUP_DESCRIPTION",
                "ASSET_NUMBER",
                "ASSET_DESCRIPTION",
            }
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(f"Source CSV is missing column(s): {sorted(missing)}")

            assets: set[tuple[str, str, str, str, str | None]] = set()
            expected_org = org_code.strip().upper() if org_code else None
            for row in reader:
                if expected_org and "ORGANIZATION_CODE" in row:
                    row_org = (row.get("ORGANIZATION_CODE") or "").strip().upper()
                    if row_org != expected_org:
                        continue
                if area_codes:
                    row_area = normalize_text(row.get("DEPARTMENT_CODE"))
                    if row_area not in area_codes:
                        continue
                area = normalize_text(row.get("DEPARTMENT_CODE")) or DEFAULT_UNKNOWN_AREA
                equipment_group = normalize_text(row.get("ASSET_GROUP_DESCRIPTION"))
                asset = normalize_asset_number(row.get("ASSET_NUMBER"))
                description = row.get("ASSET_DESCRIPTION")
                model = derive_model(description)
                if not equipment_group or not asset or not model:
                    continue
                assets.add((area, equipment_group, model, asset, description))

        return populate_target(target, assets)
    finally:
        target.close()


def main() -> int:
    args = parse_args()
    area_codes = None
    if args.area_codes:
        area_codes = {
            normalized
            for code in args.area_codes.split(",")
            if (normalized := normalize_text(code))
        }
    if args.source_csv:
        counts = build_hierarchy_from_csv(
            Path(args.source_csv),
            Path(args.target_db),
            args.org_code,
            area_codes,
        )
        print(f"Source CSV: {args.source_csv}")
        if args.org_code:
            print(f"Organization filter: {args.org_code.strip().upper()}")
        if area_codes:
            print(f"Area filter: {', '.join(sorted(area_codes))}")
    else:
        counts = build_hierarchy(Path(args.source_db), Path(args.target_db))
        print(f"Source database: {args.source_db}")
    print(f"Target database: {args.target_db}")
    for table, count in counts.items():
        print(f"{table} rows: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
