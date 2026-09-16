"""Create the normalized bom table with position_id links."""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


REMOVED_SOURCE_COLUMNS = {
    "matched_operation_seq",
    "bill_sequence_id",
    "common_bill_sequence_id",
    "alternate_bom_designator",
    "assembly_type",
    "item_num",
    "component_sequence_id",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Create bom from boms_for_department using area/equipment_group/model/"
            "asset_number hierarchy and position_id."
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
        f"{db_path.stem}_before_bom_table_{stamp}{db_path.suffix}"
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


def require_schema(connection: sqlite3.Connection) -> None:
    for table_name in ("boms_for_department", "position", "area", "equipment_group", "model"):
        if not table_exists(connection, table_name):
            raise SystemExit(f"Missing required table: {table_name}")

    required_source = {
        "id",
        "department_code",
        "asset_number",
        "asset_description",
        "asset_group_item",
        "part_number",
        "part_description",
        "component_quantity",
        "component_uom",
        "component_yield_factor",
        "component_remarks",
        "effectivity_date",
        "disable_date",
        "currently_active",
        "source_file",
        "loaded_at_utc",
    }
    missing_source = required_source - columns_for(connection, "boms_for_department")
    if missing_source:
        raise SystemExit(
            f"boms_for_department is missing column(s): {sorted(missing_source)}"
        )


def rebuild_bom(connection: sqlite3.Connection) -> None:
    require_schema(connection)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("DROP TABLE IF EXISTS bom")
    connection.execute(
        """
        CREATE TABLE bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_bom_id INTEGER NOT NULL,
            position_id INTEGER,
            area TEXT,
            equipment_group TEXT,
            model TEXT,
            asset_number TEXT,
            asset_description TEXT,
            part_number TEXT,
            part_description TEXT,
            component_quantity TEXT,
            component_uom TEXT,
            component_yield_factor TEXT,
            component_remarks TEXT,
            effectivity_date TEXT,
            disable_date TEXT,
            currently_active TEXT,
            source_file TEXT,
            loaded_at_utc TEXT,
            FOREIGN KEY (position_id)
                REFERENCES position (id),
            UNIQUE (source_bom_id)
        )
        """
    )
    connection.execute(
        """
        INSERT INTO bom (
            source_bom_id,
            position_id,
            area,
            equipment_group,
            model,
            asset_number,
            asset_description,
            part_number,
            part_description,
            component_quantity,
            component_uom,
            component_yield_factor,
            component_remarks,
            effectivity_date,
            disable_date,
            currently_active,
            source_file,
            loaded_at_utc
        )
        WITH position_asset AS (
            SELECT
                p.id AS position_id,
                an.asset_number,
                a.area,
                eg.equipment_group,
                m.model
            FROM position p
            JOIN asset_number an
              ON an.asset_number_id = p.asset_number_id
            LEFT JOIN area a
              ON a.area_id = p.area_id
            LEFT JOIN equipment_group eg
              ON eg.equipment_group_id = p.equipment_group_id
            LEFT JOIN model m
              ON m.model_id = p.model_id
        ),
        ranked_position AS (
            SELECT
                b.id AS source_bom_id,
                pa.position_id,
                pa.area,
                pa.equipment_group,
                pa.model,
                pa.asset_number AS position_asset_number,
                ROW_NUMBER() OVER (
                    PARTITION BY b.id
                    ORDER BY
                        CASE
                            WHEN pa.area = b.department_code
                             AND pa.equipment_group = b.asset_group_item
                            THEN 1
                            WHEN pa.area = b.department_code
                            THEN 2
                            WHEN pa.equipment_group = b.asset_group_item
                            THEN 3
                            ELSE 4
                        END,
                        pa.position_id
                ) AS position_rank
            FROM boms_for_department b
            JOIN position_asset pa
              ON pa.asset_number = b.asset_number
        )
        SELECT
            b.id AS source_bom_id,
            rp.position_id,
            rp.area,
            rp.equipment_group,
            rp.model,
            COALESCE(rp.position_asset_number, b.asset_number) AS asset_number,
            b.asset_description,
            b.part_number,
            b.part_description,
            b.component_quantity,
            b.component_uom,
            b.component_yield_factor,
            b.component_remarks,
            b.effectivity_date,
            b.disable_date,
            b.currently_active,
            b.source_file,
            b.loaded_at_utc
        FROM boms_for_department b
        LEFT JOIN ranked_position rp
          ON rp.source_bom_id = b.id
         AND rp.position_rank = 1
        ORDER BY b.id
        """
    )
    connection.execute("CREATE INDEX idx_bom_position_id ON bom (position_id)")
    connection.execute("CREATE INDEX idx_bom_area ON bom (area)")
    connection.execute("CREATE INDEX idx_bom_equipment_group ON bom (equipment_group)")
    connection.execute("CREATE INDEX idx_bom_model ON bom (model)")
    connection.execute("CREATE INDEX idx_bom_asset_number ON bom (asset_number)")
    connection.execute("CREATE INDEX idx_bom_part_number ON bom (part_number)")
    connection.execute("CREATE INDEX idx_bom_currently_active ON bom (currently_active)")
    connection.commit()


def print_validation(connection: sqlite3.Connection) -> None:
    source_columns = columns_for(connection, "boms_for_department")
    bom_columns = columns_for(connection, "bom")
    checks = [
        ("bom rows", "SELECT COUNT(*) FROM bom"),
        ("source rows", "SELECT COUNT(*) FROM boms_for_department"),
        ("bom rows missing position_id", "SELECT COUNT(*) FROM bom WHERE position_id IS NULL"),
        (
            "bom position orphan foreign keys",
            """
            SELECT COUNT(*)
            FROM bom b
            LEFT JOIN position p
              ON p.id = b.position_id
            WHERE b.position_id IS NOT NULL
              AND p.id IS NULL
            """,
        ),
        ("foreign_key_check rows", "SELECT COUNT(*) FROM pragma_foreign_key_check"),
    ]
    for label, query in checks:
        print(f"{label}: {connection.execute(query).fetchone()[0]}")

    removed_present = sorted(REMOVED_SOURCE_COLUMNS & bom_columns)
    print(f"removed columns still in bom: {removed_present}")
    print(f"source-only hierarchy columns replaced: {sorted({'department_code', 'asset_group_item'} & source_columns)}")
    print(f"bom columns: {', '.join(row[1] for row in connection.execute('PRAGMA table_info(bom)'))}")


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    backup_path = None
    if not args.no_backup:
        backup_path = make_backup(db_path)

    with sqlite3.connect(db_path) as connection:
        rebuild_bom(connection)
        print_validation(connection)

    if backup_path:
        print(f"Backup created: {backup_path}")
    print(f"Updated database: {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
