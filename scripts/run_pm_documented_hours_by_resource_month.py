from __future__ import annotations

import argparse
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configuration.config import OUTPUT_BASE_DIR, SQL_DIR, ensure_output_dirs
from configuration.orcdb_logger import info, set_request_id, timed_operation
from configuration.utils.report_utility import ReportUtility
from oracledb_connector import OracleDBConnector


OUTPUT_DIR = OUTPUT_BASE_DIR / "pm_documented_hours_by_resource_month"


def _sql_literal(value: object, sql_kind: str = "string", upper: bool = False) -> str:
    if sql_kind == "int":
        return str(int(value))

    text = str(value).strip()
    if upper:
        text = text.upper()
    text = text.replace("'", "''")
    return f"'{text}'"


def _render_sql(template_name: str, replacements: dict[str, str]) -> str:
    template_path = SQL_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"Missing SQL template: {template_path}")

    sql_text = template_path.read_text(encoding="utf-8")
    for token, value in replacements.items():
        sql_text = sql_text.replace(f"__{token}__", value)
    return sql_text


def _run_sql_to_dataframe(oracle: OracleDBConnector, sql_text: str) -> pd.DataFrame:
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".sql",
        delete=False,
        encoding="utf-8",
    ) as tmp_sql:
        tmp_sql.write(sql_text)
        tmp_sql_path = Path(tmp_sql.name)

    with tempfile.NamedTemporaryFile(
        suffix=".csv",
        delete=False,
    ) as tmp_csv:
        tmp_csv_path = Path(tmp_csv.name)

    try:
        result = oracle.run_sql_script(str(tmp_sql_path), str(tmp_csv_path))
        if result.returncode != 0:
            raise RuntimeError(
                f"SQLcl execution failed: {(result.stderr or result.stdout).strip()}"
            )
        if not tmp_csv_path.exists() or tmp_csv_path.stat().st_size == 0:
            raise RuntimeError("Query produced no CSV output")
        return pd.read_csv(tmp_csv_path)
    finally:
        tmp_sql_path.unlink(missing_ok=True)
        tmp_csv_path.unlink(missing_ok=True)


def _build_summary(detail_df: pd.DataFrame) -> pd.DataFrame:
    if detail_df.empty:
        return pd.DataFrame()

    work_order_counts = (
        detail_df.groupby(["RESOURCE_CODE", "RESOURCE_DESCRIPTION"])["WORK_ORDER"]
        .nunique()
        .rename("WORK_ORDER_COUNT")
    )
    planned_work_order_counts = (
        detail_df[detail_df["MAINTENANCE_SPLIT"] == "PLANNED"]
        .groupby(["RESOURCE_CODE", "RESOURCE_DESCRIPTION"])["WORK_ORDER"]
        .nunique()
        .rename("PLANNED_WORK_ORDER_COUNT")
    )
    reactive_work_order_counts = (
        detail_df[detail_df["MAINTENANCE_SPLIT"] == "REACTIVE"]
        .groupby(["RESOURCE_CODE", "RESOURCE_DESCRIPTION"])["WORK_ORDER"]
        .nunique()
        .rename("REACTIVE_WORK_ORDER_COUNT")
    )
    line_counts = (
        detail_df.groupby(["RESOURCE_CODE", "RESOURCE_DESCRIPTION"])
        .size()
        .rename("RESOURCE_LINE_COUNT")
    )
    hour_totals = (
        detail_df.groupby(["RESOURCE_CODE", "RESOURCE_DESCRIPTION"])["DOCUMENTED_HOURS"]
        .sum()
        .rename("TOTAL_DOCUMENTED_HOURS")
    )
    planned_hour_totals = (
        detail_df[detail_df["MAINTENANCE_SPLIT"] == "PLANNED"]
        .groupby(["RESOURCE_CODE", "RESOURCE_DESCRIPTION"])["DOCUMENTED_HOURS"]
        .sum()
        .rename("PLANNED_DOCUMENTED_HOURS")
    )
    reactive_hour_totals = (
        detail_df[detail_df["MAINTENANCE_SPLIT"] == "REACTIVE"]
        .groupby(["RESOURCE_CODE", "RESOURCE_DESCRIPTION"])["DOCUMENTED_HOURS"]
        .sum()
        .rename("REACTIVE_DOCUMENTED_HOURS")
    )
    monthly_hours = detail_df.pivot_table(
        index=["RESOURCE_CODE", "RESOURCE_DESCRIPTION"],
        columns="WORK_ORDER_MONTH",
        values="DOCUMENTED_HOURS",
        aggfunc="sum",
        fill_value=0,
    )

    summary = pd.concat(
        [
            work_order_counts,
            planned_work_order_counts,
            reactive_work_order_counts,
            line_counts,
            hour_totals,
            planned_hour_totals,
            reactive_hour_totals,
            monthly_hours,
        ],
        axis=1,
    ).fillna(0)
    summary = summary.reset_index()
    summary = summary.sort_values(
        ["TOTAL_DOCUMENTED_HOURS", "RESOURCE_CODE"],
        ascending=[False, True],
    )
    return summary


def _resource_sheet_name(resource_code: object, resource_description: object) -> str:
    code = str(resource_code).strip()
    description = str(resource_description).strip()
    if code:
        return code
    if description:
        return description
    return "Resource"


def build_workbook(org_code: str, months: int) -> Path:
    set_request_id()
    ensure_output_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workbook_path = OUTPUT_DIR / f"documented_hours_by_resource_booklet_{timestamp}.xlsx"

    detail_sql = _render_sql(
        "pm_documented_hours_by_resource_detail.sql",
        {
            "ORG_CODE": _sql_literal(org_code, upper=True),
            "MONTHS": _sql_literal(months, sql_kind="int"),
        },
    )

    oracle = OracleDBConnector()

    with timed_operation("documented_hours_by_resource_booklet"):
        info(f"Building documented-hours resource workbook | org_code={org_code.upper()} months={months}")
        detail_df = _run_sql_to_dataframe(oracle, detail_sql)
        if detail_df.empty:
            raise RuntimeError("Documented-hours resource detail returned no rows")

        detail_df["DOCUMENTED_HOURS"] = pd.to_numeric(
            detail_df["DOCUMENTED_HOURS"],
            errors="coerce",
        ).fillna(0)

        sheets: list[tuple[str, pd.DataFrame]] = [("Summary", _build_summary(detail_df))]
        for (resource_code, resource_description), resource_df in detail_df.groupby(
            ["RESOURCE_CODE", "RESOURCE_DESCRIPTION"],
            dropna=False,
            sort=True,
        ):
            sheet_name = _resource_sheet_name(resource_code, resource_description)
            sheets.append((sheet_name, resource_df.sort_values(["WORK_ORDER_MONTH", "MAINTENANCE_SPLIT", "WORK_ORDER"])))

        ReportUtility.dataframes_to_excel(sheets=sheets, excel_path=workbook_path)
        info(f"Workbook complete: {workbook_path}")

    return workbook_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Build an Excel booklet with documented work-order hours summary and one sheet per resource."
        )
    )
    parser.add_argument("--org-code", default="XAU", help="Organization code.")
    parser.add_argument("--months", type=int, default=12, help="Rolling number of months.")
    args = parser.parse_args()

    workbook_path = build_workbook(org_code=args.org_code, months=args.months)
    print(workbook_path)


if __name__ == "__main__":
    main()
