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


OUTPUT_DIR = OUTPUT_BASE_DIR / "asset_maintenance_burden_summary"


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


def _sql_in_list(values: list[object]) -> str:
    return ", ".join(_sql_literal(value) for value in values)


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


def build_workbook(
    org_code: str,
    months: int,
    limit: int,
    summary_only: bool = False,
    include_parts: bool = True,
    include_time_transactions: bool = False,
) -> Path:
    set_request_id()
    ensure_output_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    workbook_path = OUTPUT_DIR / f"asset_maintenance_burden_summary_{timestamp}.xlsx"

    oracle = OracleDBConnector()

    with timed_operation("asset_maintenance_burden_workbook"):
        info(
            f"Building asset maintenance burden workbook | org_code={org_code.upper()} months={months} limit={limit}"
        )

        summary_sql = _render_sql(
            "asset_maintenance_burden_summary.sql",
            {
                "ORG_CODE": _sql_literal(org_code, upper=True),
                "MONTHS": _sql_literal(months, sql_kind="int"),
                "LIMIT": _sql_literal(limit, sql_kind="int"),
            },
        )
        summary_df = _run_sql_to_dataframe(oracle, summary_sql)
        if summary_df.empty:
            raise RuntimeError("Asset maintenance burden summary returned no rows")

        sheets: list[tuple[str, pd.DataFrame]] = [("Summary", summary_df)]
        asset_numbers = [row["ASSET_NUMBER"] for _, row in summary_df.iterrows()]

        if include_parts and not summary_only:
            parts_sql = _render_sql(
                "asset_maintenance_burden_parts.sql",
                {
                    "ORG_CODE": _sql_literal(org_code, upper=True),
                    "ASSET_NUMBERS": _sql_in_list(asset_numbers),
                    "MONTHS": _sql_literal(months, sql_kind="int"),
                },
            )
            parts_df = _run_sql_to_dataframe(oracle, parts_sql)
            sheets.append(("Parts", parts_df))

        if not summary_only:
            for asset_number in asset_numbers:
                detail_sql = _render_sql(
                    "asset_maintenance_burden_detail.sql",
                    {
                        "ORG_CODE": _sql_literal(org_code, upper=True),
                        "ASSET_NUMBER": _sql_literal(asset_number),
                        "MONTHS": _sql_literal(months, sql_kind="int"),
                    },
                )
                detail_df = _run_sql_to_dataframe(oracle, detail_sql)
                sheets.append((str(asset_number), detail_df))

                if include_time_transactions:
                    time_txn_sql = _render_sql(
                        "asset_maintenance_burden_time_transactions.sql",
                        {
                            "ORG_CODE": _sql_literal(org_code, upper=True),
                            "ASSET_NUMBER": _sql_literal(asset_number),
                            "MONTHS": _sql_literal(months, sql_kind="int"),
                        },
                    )
                    time_txn_df = _run_sql_to_dataframe(oracle, time_txn_sql)
                    sheets.append((f"{asset_number}_TimeTxn", time_txn_df))

        ReportUtility.dataframes_to_excel(sheets=sheets, excel_path=workbook_path)
        info(f"Workbook complete: {workbook_path}")

    return workbook_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Asset maintenance burden workbook with summary, parts, and one sheet per top asset. "
            "Work-order detail rows include QA location and description of work performed when available."
        )
    )
    parser.add_argument("--org-code", default="XAU", help="Organization code.")
    parser.add_argument("--months", type=int, default=12, help="Rolling number of months.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of assets.")
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Create only the ranked summary sheet. This is faster for 12-month time analysis.",
    )
    parser.add_argument(
        "--no-parts",
        action="store_true",
        help="Do not add the parts frequency sheet.",
    )
    parser.add_argument(
        "--include-time-transactions",
        action="store_true",
        help="Add raw posted/pending time transaction sheets for each selected asset.",
    )
    args = parser.parse_args()

    workbook_path = build_workbook(
        org_code=args.org_code,
        months=args.months,
        limit=args.limit,
        summary_only=args.summary_only,
        include_parts=not args.no_parts,
        include_time_transactions=args.include_time_transactions,
    )
    print(workbook_path)


if __name__ == "__main__":
    main()
