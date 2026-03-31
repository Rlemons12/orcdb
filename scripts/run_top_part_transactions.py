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


OUTPUT_DIR = OUTPUT_BASE_DIR / "top_part_transactions"


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


def build_workbook(org_code: str, days: int, limit: int) -> Path:
    set_request_id()
    ensure_output_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workbook_path = OUTPUT_DIR / f"top_part_transactions_detail_{timestamp}.xlsx"

    replacements = {
        "ORG_CODE": _sql_literal(org_code, upper=True),
        "DAYS": _sql_literal(days, sql_kind="int"),
        "LIMIT": _sql_literal(limit, sql_kind="int"),
    }

    oracle = OracleDBConnector()

    with timed_operation("top_part_transactions_workbook"):
        info(
            f"Building top part transactions workbook | org_code={org_code.upper()} days={days} limit={limit}"
        )

        summary_sql = _render_sql("top_part_transactions_summary.sql", replacements)
        summary_df = _run_sql_to_dataframe(oracle, summary_sql)
        if summary_df.empty:
            raise RuntimeError("Top part transactions query returned no rows")

        sheets: list[tuple[str, pd.DataFrame]] = [("Summary", summary_df)]
        for work_order in summary_df["WORK_ORDER"].tolist():
            detail_sql = _render_sql(
                "top_part_transactions_detail.sql",
                {
                    "ORG_CODE": _sql_literal(org_code, upper=True),
                    "WORK_ORDER": _sql_literal(work_order),
                    "DAYS": _sql_literal(days, sql_kind="int"),
                },
            )
            detail_df = _run_sql_to_dataframe(oracle, detail_sql)
            sheets.append((str(work_order), detail_df))

        ReportUtility.dataframes_to_excel(sheets=sheets, excel_path=workbook_path)
        info(f"Workbook complete: {workbook_path}")

    return workbook_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build a workbook for the top work orders by part transactions."
    )
    parser.add_argument("--org-code", default="XAU", help="Organization code.")
    parser.add_argument("--days", type=int, default=30, help="Rolling number of days.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of work orders.")
    args = parser.parse_args()

    workbook_path = build_workbook(
        org_code=args.org_code,
        days=args.days,
        limit=args.limit,
    )
    print(workbook_path)


if __name__ == "__main__":
    main()
