"""Export hierarchy and position mapper sheets to an Excel workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import sqlite3


DEFAULT_DB = "data/BOM.db"
DEFAULT_OUTPUT = "data/position_load_template.xlsx"
EXCEL_MAX_ROWS = 1_048_576
EXCEL_DATA_ROWS_PER_SHEET = EXCEL_MAX_ROWS - 1
BOM_CHUNK_SIZE = 100_000

BOM_QUERY = """
SELECT
    id AS bom_id,
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
FROM bom
ORDER BY
    position_id,
    asset_number,
    part_number,
    bom_id
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Export position, area, equipment_group, model, and asset sheets "
            "from BOM.db."
        )
    )
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite database path.")
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Excel workbook output path.",
    )
    return parser.parse_args()


def read_sql(connection: sqlite3.Connection, query: str) -> pd.DataFrame:
    return pd.read_sql_query(query, connection)


def size_columns(worksheet) -> None:
    for column_cells in worksheet.columns:
        values = [str(cell.value) if cell.value is not None else "" for cell in column_cells]
        width = min(max(len(value) for value in values) + 2, 60)
        worksheet.column_dimensions[column_cells[0].column_letter].width = width


def write_dataframe(writer: pd.ExcelWriter, sheet_name: str, df: pd.DataFrame) -> None:
    df.to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    worksheet.freeze_panes = "A2"
    size_columns(worksheet)


def write_bom_sheets(
    connection: sqlite3.Connection,
    writer: pd.ExcelWriter,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    sheet_number = 1
    current_sheet = f"bom_{sheet_number}"
    current_row = 0
    current_count = 0

    for chunk in pd.read_sql_query(BOM_QUERY, connection, chunksize=BOM_CHUNK_SIZE):
        start = 0
        while start < len(chunk):
            remaining = EXCEL_DATA_ROWS_PER_SHEET - current_count
            part = chunk.iloc[start : start + remaining]
            header = current_row == 0
            part.to_excel(
                writer,
                sheet_name=current_sheet,
                index=False,
                header=header,
                startrow=current_row,
            )
            written = len(part)
            current_row += written + (1 if header else 0)
            current_count += written
            start += written

            if current_count == EXCEL_DATA_ROWS_PER_SHEET:
                worksheet = writer.sheets[current_sheet]
                worksheet.freeze_panes = "A2"
                for idx, column_name in enumerate(chunk.columns, start=1):
                    worksheet.column_dimensions[
                        worksheet.cell(row=1, column=idx).column_letter
                    ].width = min(max(len(str(column_name)) + 2, 12), 40)
                counts[current_sheet] = current_count
                sheet_number += 1
                current_sheet = f"bom_{sheet_number}"
                current_row = 0
                current_count = 0

    if current_count > 0:
        worksheet = writer.sheets[current_sheet]
        worksheet.freeze_panes = "A2"
        for idx, column_name in enumerate(pd.read_sql_query(BOM_QUERY + " LIMIT 0", connection).columns, start=1):
            worksheet.column_dimensions[
                worksheet.cell(row=1, column=idx).column_letter
            ].width = min(max(len(str(column_name)) + 2, 12), 40)
        counts[current_sheet] = current_count

    return counts


def export_workbook(db_path: Path, output_path: Path) -> dict[str, int]:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        sheets = {
            "position": read_sql(
                connection,
                """
                SELECT
                    p.id AS position_id,
                    p.area_id,
                    a.area,
                    p.equipment_group_id,
                    eg.equipment_group,
                    p.model_id,
                    m.model,
                    p.asset_number_id,
                    p.location_id,
                    p.subassembly_id,
                    p.component_assembly_id,
                    p.assembly_view_id,
                    p.site_location_id,
                    p.campus_id,
                    p.building_id
                FROM position p
                LEFT JOIN area a
                  ON a.area_id = p.area_id
                LEFT JOIN equipment_group eg
                  ON eg.equipment_group_id = p.equipment_group_id
                LEFT JOIN model m
                  ON m.model_id = p.model_id
                ORDER BY
                    p.id
                """,
            ),
            "area": read_sql(
                connection,
                """
                SELECT
                    area_id,
                    area
                FROM area
                ORDER BY area
                """,
            ),
            "equipment_group": read_sql(
                connection,
                """
                SELECT
                    eg.equipment_group_id,
                    eg.area_id,
                    a.area,
                    eg.equipment_group,
                    eg.equipment_group_description
                FROM equipment_group eg
                LEFT JOIN area a
                  ON a.area_id = eg.area_id
                ORDER BY
                    a.area,
                    eg.equipment_group
                """,
            ),
            "model": read_sql(
                connection,
                """
                SELECT
                    m.model_id,
                    m.equipment_group_id,
                    eg.equipment_group,
                    eg.area_id,
                    a.area,
                    m.model
                FROM model m
                LEFT JOIN equipment_group eg
                  ON eg.equipment_group_id = m.equipment_group_id
                LEFT JOIN area a
                  ON a.area_id = eg.area_id
                ORDER BY
                    a.area,
                    eg.equipment_group,
                    m.model
                """,
            ),
            "asset": read_sql(
                connection,
                """
                SELECT
                    an.model_id,
                    an.asset_number_id,
                    m.model,
                    eg.equipment_group_id,
                    eg.equipment_group,
                    a.area_id,
                    a.area,
                    an.asset_number,
                    an.asset_description
                FROM asset_number an
                LEFT JOIN model m
                  ON m.model_id = an.model_id
                LEFT JOIN equipment_group eg
                  ON eg.equipment_group_id = m.equipment_group_id
                LEFT JOIN area a
                  ON a.area_id = eg.area_id
                ORDER BY
                    a.area,
                    eg.equipment_group,
                    m.model,
                    an.asset_number
                """,
            ),
            "drawing": read_sql(
                connection,
                """
                SELECT
                    d.position_id,
                    d.area,
                    d.equipment_group,
                    d.model,
                    d.asset_number,
                    d.stations,
                    d.equipment_name,
                    d.drawing_number,
                    d.drawing_name,
                    d.revision,
                    d.cc_required,
                    d.spare_part_number
                FROM drawing d
                ORDER BY
                    d.position_id,
                    d.asset_number,
                    d.drawing_number
                """,
            ),
        }

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                write_dataframe(writer, sheet_name, df)
            bom_counts = write_bom_sheets(connection, writer)

    counts = {sheet_name: len(df) for sheet_name, df in sheets.items()}
    counts.update(bom_counts)
    return counts


def main() -> int:
    args = parse_args()
    db_path = Path(args.db)
    output_path = Path(args.output)
    if not db_path.exists():
        raise SystemExit(f"Database does not exist: {db_path}")

    counts = export_workbook(db_path, output_path)
    print(f"Workbook created: {output_path}")
    for sheet_name, count in counts.items():
        print(f"{sheet_name} rows: {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
