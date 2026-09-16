from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configuration.config import OUTPUT_BASE_DIR, ensure_output_dirs
from configuration.orcdb_logger import error, info, set_request_id, timed_operation
from configuration.utils.report_utility import ReportUtility
from oracledb_connector import OracleDBConnector


OUTPUT_DIR = OUTPUT_BASE_DIR / "configured_boms_for_department"
DELIM = "~|~"


def sql_literal(value: object) -> str:
    return "'" + str(value).strip().replace("'", "''") + "'"


def clean_sql_text(value: str) -> str:
    return " ".join(str(value or "").replace("\r", " ").replace("\n", " ").split())


def clean_csv(csv_path: Path) -> int:
    lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()
    start = 0
    for index, line in enumerate(lines):
        if line.strip() and "," in line:
            start = index
            break
    csv_path.write_text("\n".join(lines[start:]) + "\n", encoding="utf-8")
    return start


def fetch_department_assets(
    oracle: OracleDBConnector,
    org_code: str,
    department_code: str,
    operation_seq: int,
    work_order_status: str,
) -> list[dict[str, str]]:
    status_filter = ""
    if work_order_status.upper() != "ALL":
        status_filter = f"      AND EWO.WORK_ORDER_STATUS = {sql_literal(work_order_status)}\n"

    sql = f"""
    SELECT DISTINCT
        TO_CHAR(EWO.ORGANIZATION_ID) || '{DELIM}' ||
        WO.DEPARTMENT_CODE || '{DELIM}' ||
        TO_CHAR(WO.OPERATION_SEQ_NUM) || '{DELIM}' ||
        EWO.ASSET_NUMBER || '{DELIM}' ||
        REPLACE(REPLACE(NVL(EWO.ASSET_DESCRIPTION, ''), CHR(10), ' '), CHR(13), ' ') || '{DELIM}' ||
        TO_CHAR(EWO.ASSET_GROUP_ID)
    FROM APPS.WIP_OPERATIONS_V WO
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.WIP_ENTITY_ID = WO.WIP_ENTITY_ID
       AND EWO.ORGANIZATION_ID = WO.ORGANIZATION_ID
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = {sql_literal(org_code)}
      AND WO.DEPARTMENT_CODE = {sql_literal(department_code)}
      AND ({operation_seq} = 0 OR WO.OPERATION_SEQ_NUM = {operation_seq})
      AND EWO.WIP_ENTITY_NAME LIKE 'PM%'
{status_filter.rstrip()}
      AND EWO.ASSET_NUMBER IS NOT NULL
      AND EWO.ASSET_GROUP_ID IS NOT NULL
    """
    ok, out = oracle.run_query(sql)
    if not ok or "ORA-" in out or "SP2-" in out:
        raise RuntimeError(out)

    assets: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for line in out.splitlines():
        if DELIM not in line:
            continue
        parts = line.strip().split(DELIM)
        if len(parts) != 6:
            continue
        row = {
            "organization_id": parts[0],
            "department_code": parts[1],
            "operation_seq": parts[2],
            "asset_number": parts[3],
            "asset_description": clean_sql_text(parts[4]),
            "asset_group_id": parts[5],
        }
        key = (row["organization_id"], row["asset_number"], row["asset_group_id"])
        if key in seen:
            continue
        seen.add(key)
        assets.append(row)
    return assets


def build_asset_cte(assets: list[dict[str, str]]) -> str:
    selects: list[str] = []
    for row in assets:
        selects.append(
            "SELECT "
            f"{int(row['organization_id'])} AS ORGANIZATION_ID, "
            f"{sql_literal(row['department_code'])} AS DEPARTMENT_CODE, "
            f"{int(row['operation_seq'])} AS MATCHED_OPERATION_SEQ, "
            f"{sql_literal(row['asset_number'])} AS ASSET_NUMBER, "
            f"{sql_literal(row['asset_description'])} AS ASSET_DESCRIPTION, "
            f"{int(row['asset_group_id'])} AS ASSET_GROUP_ID "
            "FROM DUAL"
        )
    return "\nUNION ALL\n".join(selects)


def build_bom_sql(asset_cte: str, active_only: int) -> str:
    active_filter = """
WHERE BIC.EFFECTIVITY_DATE <= SYSDATE
  AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
""" if active_only else ""

    return f"""
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET DEFINE OFF
SET SQLFORMAT CSV

WITH DEPT_ASSETS AS (
{asset_cte}
)
SELECT
    DA.DEPARTMENT_CODE,
    DA.MATCHED_OPERATION_SEQ,
    DA.ASSET_NUMBER,
    DA.ASSET_DESCRIPTION,
    AG.SEGMENT1 AS ASSET_GROUP_ITEM,
    AG.DESCRIPTION AS ASSET_GROUP_DESCRIPTION,
    BBOM.BILL_SEQUENCE_ID,
    BBOM.COMMON_BILL_SEQUENCE_ID,
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BBOM.ASSEMBLY_TYPE,
    BIC.ITEM_NUM,
    BIC.COMPONENT_SEQUENCE_ID,
    COMP.SEGMENT1 AS PART_NUMBER,
    COMP.DESCRIPTION AS PART_DESCRIPTION,
    BIC.COMPONENT_QUANTITY,
    COMP.PRIMARY_UOM_CODE AS COMPONENT_UOM,
    BIC.COMPONENT_YIELD_FACTOR,
    BIC.COMPONENT_REMARKS,
    TO_CHAR(BIC.EFFECTIVITY_DATE, 'MM/DD/YYYY') AS EFFECTIVITY_DATE,
    TO_CHAR(BIC.DISABLE_DATE, 'MM/DD/YYYY') AS DISABLE_DATE,
    CASE
        WHEN BIC.EFFECTIVITY_DATE <= SYSDATE
         AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
        THEN 'Y'
        ELSE 'N'
    END AS CURRENTLY_ACTIVE
FROM DEPT_ASSETS DA
JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
    ON BBOM.ASSEMBLY_ITEM_ID = DA.ASSET_GROUP_ID
   AND BBOM.ORGANIZATION_ID = DA.ORGANIZATION_ID
JOIN APPS.BOM_INVENTORY_COMPONENTS BIC
    ON BIC.BILL_SEQUENCE_ID = BBOM.COMMON_BILL_SEQUENCE_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B AG
    ON AG.INVENTORY_ITEM_ID = DA.ASSET_GROUP_ID
   AND AG.ORGANIZATION_ID = DA.ORGANIZATION_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B COMP
    ON COMP.INVENTORY_ITEM_ID = BIC.COMPONENT_ITEM_ID
   AND COMP.ORGANIZATION_ID = DA.ORGANIZATION_ID
{active_filter}
ORDER BY
    DA.DEPARTMENT_CODE,
    DA.ASSET_NUMBER,
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BIC.ITEM_NUM,
    COMP.SEGMENT1
;
EXIT
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Official configured BOMs for released PM assets in a department code."
    )
    parser.add_argument("--org-code", default="XAU", help="Organization code.")
    parser.add_argument("--department-code", required=True, help="Department code, such as MMLFL or MMCBF.")
    parser.add_argument("--operation-seq", type=int, default=10, help="Operation sequence. Use 0 for all operations.")
    parser.add_argument("--active-only", type=int, default=1, help="Use 1 for active BOM components only, 0 for all.")
    parser.add_argument("--work-order-status", default="Released", help="Work order status to source assets from. Use ALL for any status.")
    args = parser.parse_args()

    org_code = args.org_code.upper()
    department_code = args.department_code.upper()

    set_request_id()
    ensure_output_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = OUTPUT_DIR / f"configured_boms_for_department_{department_code}_{timestamp}.csv"
    excel_file = OUTPUT_DIR / f"configured_boms_for_department_{department_code}_{timestamp}.xlsx"

    oracle = OracleDBConnector()

    info(f"Finding released PM assets for department {department_code}")
    with timed_operation("department_asset_list"):
        assets = fetch_department_assets(
            oracle,
            org_code,
            department_code,
            args.operation_seq,
            args.work_order_status,
        )

    if not assets:
        raise RuntimeError(f"No released PM assets found for department {department_code}")

    info(f"Found {len(assets)} distinct asset/group rows for {department_code}")
    info(f"CSV output: {csv_file}")
    info(f"Excel output: {excel_file}")

    bom_sql = build_bom_sql(build_asset_cte(assets), int(args.active_only))
    cmd = [oracle.sqlcl_path, "-S", oracle.connect_string]

    with timed_operation("configured_boms_for_department_export"):
        with csv_file.open("w", encoding="utf-8", errors="replace", newline="") as stdout_file:
            result = subprocess.run(
                cmd,
                input=bom_sql,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=stdout_file,
                stderr=subprocess.PIPE,
                timeout=1800,
            )

    if result.returncode != 0:
        error((result.stderr or "").strip())
        raise RuntimeError("SQLcl execution failed")

    if not csv_file.exists() or csv_file.stat().st_size == 0:
        raise RuntimeError(f"No CSV output created: {csv_file}")

    stripped = clean_csv(csv_file)
    info(f"Stripped {stripped} SQLcl banner line(s)")

    with timed_operation("configured_boms_for_department_excel"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name="Department BOMs",
            autosize_columns=False,
        )

    info(f"Report complete: {excel_file}")


if __name__ == "__main__":
    main()
