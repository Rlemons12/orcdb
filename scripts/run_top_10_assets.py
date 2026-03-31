import sys
from pathlib import Path

# Ensure the project root is on sys.path regardless of where this script is launched from
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import argparse
import tempfile
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook

from oracledb_connector import OracleDBConnector
from configuration.orcdb_logger import (
    set_request_id,
    info,
    error,
    timed_operation,
)
from configuration.config import (
    SQL_DIR,
    OUTPUT_BASE_DIR,
    ensure_output_dirs,
)
from configuration.utils.report_utility import ReportUtility


TOP10_DIR = OUTPUT_BASE_DIR / "top10_assets"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Top 10 assets by work order volume for a given org — last 12 months."
    )
    parser.add_argument(
        "--org-code",
        default="XAU",
        help="Organization code to report on (default: XAU)",
    )
    return parser.parse_args()


def build_sql(template_path: Path, org_code: str) -> Path:
    """
    Read the SQL template, replace __ORG_CODE__ with the actual org code,
    and write it to a temp file. Returns the temp file path.
    This avoids SQLcl &2 substitution issues on Windows.
    """
    sql = template_path.read_text(encoding="utf-8")
    sql = sql.replace("__ORG_CODE__", org_code)

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".sql",
        delete=False,
        encoding="utf-8"
    )
    tmp.write(sql)
    tmp.close()
    return Path(tmp.name)


def clean_csv(csv_path: Path) -> int:
    """
    Strip any SQLcl banner/status lines from the top of the CSV.
    Real CSV rows always contain a comma; SQLcl status messages do not.
    Returns the number of lines stripped.
    """
    lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()

    start = 0
    for i, line in enumerate(lines):
        if line.strip() and "," in line.strip():
            start = i
            break

    cleaned = "\n".join(lines[start:]) + "\n"
    csv_path.write_text(cleaned, encoding="utf-8")
    return start


def main():
    set_request_id()
    args = parse_args()
    org_code = args.org_code.upper().strip()

    ensure_output_dirs()
    TOP10_DIR.mkdir(parents=True, exist_ok=True)

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file   = TOP10_DIR / f"top10_assets_{org_code}_{timestamp}.csv"
    excel_file = TOP10_DIR / f"top10_assets_{org_code}_{timestamp}.xlsx"

    info("=" * 56)
    info("Top 10 Assets by Work Order Volume -- Last 12 Months")
    info("=" * 56)
    info(f"  Org code     : {org_code}")
    info(f"  Period       : last 12 months")
    info(f"  CSV output   : {csv_file}")
    info(f"  Excel output : {excel_file}")

    template = SQL_DIR / "top10_assets_wo_detail.sql"
    if not template.exists():
        error(f"SQL template not found: {template}")
        raise FileNotFoundError(f"Missing SQL template: {template}")

    oracle = OracleDBConnector()

    # Step 1 — Build temp SQL with org code baked in
    info("Step 1/4 -- Building SQL for org '{}'".format(org_code))
    tmp_sql = build_sql(template, org_code)
    info(f"  Temp SQL     : {tmp_sql}")

    # Step 2 — Execute via SQLcl (only &1 needed now)
    info("Step 2/4 -- Executing SQL via SQLcl")
    info("  Stage 1: Ranking assets by work order volume...")
    info("  Stage 2: Pulling full detail for top 10 assets...")
    info("  (This query may take 30-60 seconds)")

    with timed_operation("top10_assets_sql_execution"):
        result = oracle.run_sql_script(
            str(tmp_sql),
            str(csv_file),
        )

        # Clean up temp file
        tmp_sql.unlink(missing_ok=True)

        if result.returncode != 0:
            error("SQL execution failed")
            error(result.stderr.strip())
            raise RuntimeError("SQLcl execution failed")

    if not csv_file.exists() or csv_file.stat().st_size == 0:
        error(f"No results returned for org '{org_code}'")
        info("Check that the org code is correct and work orders exist in the last 12 months")
        info("Valid org codes: SELECT ORGANIZATION_CODE FROM APPS.MTL_PARAMETERS")
        return

    # Step 3 — Clean CSV
    info("Step 3/4 -- Cleaning SQLcl banner from CSV")
    stripped = clean_csv(csv_file)
    info(f"  Stripped {stripped} banner line(s)")
    info(f"  CSV ready    : {csv_file}")

    # Step 4 — Generate Excel with one sheet per asset
    info("Step 4/4 -- Generating Excel report (one sheet per asset)")

    df = pd.read_csv(csv_file)
    total_rows = len(df)
    info(f"  Loaded {total_rows} rows from CSV")

    with timed_operation("top10_assets_excel_generation"):
        with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:

            # Summary sheet — full dataset sorted by rank
            df.sort_values(
                ["ASSET_RANK", "ASSET_NUMBER", "WO_CREATED_DATE"],
                ascending=[True, True, False]
            ).to_excel(writer, sheet_name="All Assets", index=False)
            info("  Written sheet: All Assets")

            # One sheet per asset, named by asset number
            assets = df["ASSET_NUMBER"].dropna().unique()
            assets_sorted = sorted(
                assets,
                key=lambda a: df.loc[
                    df["ASSET_NUMBER"] == a, "ASSET_RANK"
                ].iloc[0]
            )

            for asset in assets_sorted:
                asset_df = df[df["ASSET_NUMBER"] == asset].copy()
                asset_df.sort_values(
                    "WO_CREATED_DATE", ascending=False, inplace=True
                )

                # Excel sheet names max 31 chars, no special chars
                sheet_name = str(asset)[:31]

                rank = asset_df["ASSET_RANK"].iloc[0]
                wo_count = asset_df["TOTAL_WO_COUNT_12_MONTHS"].iloc[0]

                asset_df.to_excel(writer, sheet_name=sheet_name, index=False)
                info(f"  Written sheet: {sheet_name}  "
                     f"(Rank #{rank}, {wo_count} WOs, {len(asset_df)} rows)")

    info(f"  Excel ready  : {excel_file}")

    info("=" * 56)
    info("Report complete")
    info("=" * 56)
    info("")
    info("Excel tips:")
    info("  Filter ASSET_RANK to isolate a single asset")
    info("  Sort TOTAL_WO_COUNT_12_MONTHS descending to see the ranking")
    info("  Filter TECHNICIAN to see all work done by one person")


if __name__ == "__main__":
    main()