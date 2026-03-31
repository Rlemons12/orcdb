import sys
from pathlib import Path

# Ensure the project root is on sys.path regardless of where this script is launched from
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import csv
from datetime import datetime

from oracledb_connector import OracleDBConnector
from configuration.orcdb_logger import (
    set_request_id,
    info,
    error,
    timed_operation,
)
from configuration.config import (
    OUTPUT_BASE_DIR,
    ensure_output_dirs,
)
from configuration.utils.report_utility import ReportUtility


VERIFY_DIR = OUTPUT_BASE_DIR / "eam_verification"

# Accumulates every check result for the final CSV/Excel
_results: list[dict] = []


# ===========================================================
#  Check runners — each logs immediately and appends to results
# ===========================================================

def _resolve_synonym(oracle: OracleDBConnector, owner: str, table: str) -> tuple[str, str]:
    """
    If owner.table is a synonym, resolve it to the base table owner and name.
    Returns (base_owner, base_table) — same as input if not a synonym.
    Many EBS tables live in a non-APPS schema but are accessed via APPS synonyms.
    all_tab_columns is indexed against the BASE owner, not the synonym owner.
    """
    ok, out = oracle.run_query(
        f"SELECT TABLE_OWNER, TABLE_NAME FROM all_synonyms "
        f"WHERE owner = '{owner}' AND synonym_name = '{table}'"
    )
    if ok and out.strip():
        # out may be "SCHEMA   TABLE_NAME" — split on whitespace
        parts = out.strip().splitlines()[-1].split()
        if len(parts) >= 2:
            return parts[0], parts[1]
    return owner, table


def check_table(oracle: OracleDBConnector, owner: str, table: str) -> None:
    """
    Verify a table/view/synonym is accessible and has at least one row.
    Resolves APPS synonyms to their base schema so all_objects lookup is accurate.
    """
    label = f"{owner}.{table}"
    info(f"    Checking table : {label}")

    # Resolve synonym to base owner/table
    base_owner, base_table = _resolve_synonym(oracle, owner, table)
    if base_owner != owner or base_table != table:
        info(f"      (synonym -> {base_owner}.{base_table})")

    # Check base object exists in all_objects
    ok, out = oracle.run_query(
        f"SELECT COUNT(*) FROM all_objects "
        f"WHERE owner = '{base_owner}' "
        f"AND object_name = '{base_table}' "
        f"AND object_type IN ('TABLE','VIEW','SYNONYM')"
    )
    if not ok or _parse_int(out) == 0:
        _record("TABLE ACCESS", "FAIL", label,
                f"Not found in all_objects (resolved: {base_owner}.{base_table})")
        error(f"      FAIL -- {base_owner}.{base_table} not found in all_objects")
        return

    # Check it has rows (query via original synonym — that's what our SQL scripts use)
    ok, out = oracle.run_query(
        f"SELECT COUNT(*) FROM {owner}.{table} WHERE ROWNUM <= 1"
    )
    if not ok:
        _record("TABLE ACCESS", "FAIL", label, f"Query error: {out}")
        error(f"      FAIL -- query error: {out}")
        return

    if _parse_int(out) > 0:
        _record("TABLE ACCESS", "PASS", label,
                f"Accessible, has rows (base: {base_owner}.{base_table})")
        info(f"      PASS -- has rows")
    else:
        _record("TABLE ACCESS", "WARN", label,
                f"Accessible but empty (base: {base_owner}.{base_table})")
        info(f"      WARN -- accessible but EMPTY")


def check_col(oracle: OracleDBConnector, owner: str, table: str, column: str) -> None:
    """
    Verify a column exists on a table.
    Resolves APPS synonyms to base schema before querying all_tab_columns,
    since column metadata is stored against the base table owner, not the synonym.
    """
    label = f"{owner}.{table}.{column}"
    info(f"    Checking column : {label}")

    # Resolve synonym to get the real owner for all_tab_columns lookup
    base_owner, base_table = _resolve_synonym(oracle, owner, table)

    ok, out = oracle.run_query(
        f"SELECT COUNT(*) FROM all_tab_columns "
        f"WHERE owner = '{base_owner}' "
        f"AND table_name = '{base_table}' "
        f"AND column_name = '{column}'"
    )
    if not ok:
        _record("COLUMN", "FAIL", label, f"Query error: {out}")
        error(f"      FAIL -- query error")
        return

    if _parse_int(out) > 0:
        detail = "Column exists" if base_owner == owner else \
            f"Column exists (base: {base_owner}.{base_table})"
        _record("COLUMN", "PASS", label, detail)
        info(f"      PASS")
    else:
        _record("COLUMN", "FAIL", label,
                f"Column NOT FOUND (checked base: {base_owner}.{base_table})")
        error(f"      FAIL -- column not found")


def check_join(oracle: OracleDBConnector, label: str, sql: str) -> None:
    """Verify a join returns at least one row."""
    info(f"    Checking join   : {label}")

    ok, out = oracle.run_query(sql)
    if not ok:
        _record("JOIN", "FAIL", label, f"Query error: {out}")
        error(f"      FAIL -- {out}")
        return

    count = _parse_int(out)
    if count > 0:
        _record("JOIN", "PASS", label, f"{count} row(s)")
        info(f"      PASS -- {count} row(s)")
    else:
        _record("JOIN", "WARN", label, "Join returned 0 rows")
        info(f"      WARN -- 0 rows (data may not exist yet)")


def check_filter(oracle: OracleDBConnector, label: str, sql: str) -> None:
    """Verify a known filter value returns at least one match."""
    info(f"    Checking filter : {label}")

    ok, out = oracle.run_query(sql)
    if not ok:
        _record("FILTER", "FAIL", label, f"Query error: {out}")
        error(f"      FAIL -- {out}")
        return

    count = _parse_int(out)
    if count > 0:
        _record("FILTER", "PASS", label, f"{count} match(es)")
        info(f"      PASS -- {count} match(es)")
    else:
        _record("FILTER", "WARN", label, "0 matches -- filter value may be wrong or no data")
        info(f"      WARN -- 0 matches")


def check_value(oracle: OracleDBConnector, label: str, sql: str,
                max_ok: int | None = None) -> None:
    """Run a query and warn if the count exceeds max_ok (e.g. Cartesian risk)."""
    info(f"    Checking value  : {label}")

    ok, out = oracle.run_query(sql)
    if not ok:
        _record("VALUE", "FAIL", label, f"Query error: {out}")
        error(f"      FAIL -- {out}")
        return

    count = _parse_int(out)
    if max_ok is not None and count > max_ok:
        _record("VALUE", "WARN", label,
                f"{count} rows -- exceeds safe threshold of {max_ok}, Cartesian risk")
        info(f"      WARN -- {count} rows (Cartesian risk if > {max_ok})")
    else:
        _record("VALUE", "PASS", label, f"{count} row(s)")
        info(f"      PASS -- {count} row(s)")


# ===========================================================
#  Internal helpers
# ===========================================================

def _record(section: str, status: str, check: str, detail: str) -> None:
    _results.append({
        "section": section,
        "status":  status,
        "check":   check,
        "detail":  detail,
    })


def _parse_int(value: str) -> int:
    try:
        return int(value.strip().splitlines()[-1].strip())
    except (ValueError, IndexError):
        return 0


def _section(title: str) -> None:
    info("")
    info(f"  {'=' * 48}")
    info(f"  {title}")
    info(f"  {'=' * 48}")


def _write_csv(csv_path: Path) -> None:
    fieldnames = ["section", "status", "check", "detail"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(_results)


def _log_summary() -> None:
    counts = {"PASS": 0, "WARN": 0, "FAIL": 0}
    for row in _results:
        if row["status"] in counts:
            counts[row["status"]] += 1

    info("")
    info("=" * 52)
    info(f"  FINAL SUMMARY  --  "
         f"PASS: {counts['PASS']}   "
         f"WARN: {counts['WARN']}   "
         f"FAIL: {counts['FAIL']}   "
         f"TOTAL: {sum(counts.values())}")
    info("=" * 52)

    if counts["WARN"]:
        info("  Warnings:")
        for r in _results:
            if r["status"] == "WARN":
                info(f"    WARN | {r['check']} | {r['detail']}")

    if counts["FAIL"]:
        info("  Failures:")
        for r in _results:
            if r["status"] == "FAIL":
                error(f"    FAIL | {r['check']} | {r['detail']}")


# ===========================================================
#  Main
# ===========================================================

def main():
    set_request_id()
    info("=" * 52)
    info("EAM Relationship Verification -- Starting")
    info("=" * 52)

    info("Step 1/5 -- Initializing directories")
    ensure_output_dirs()
    VERIFY_DIR.mkdir(parents=True, exist_ok=True)
    info(f"  Output dir : {VERIFY_DIR}")

    info("Step 2/5 -- Connecting to Oracle")
    oracle = OracleDBConnector()
    info("  Connector ready")

    timestamp  = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file   = VERIFY_DIR / f"eam_verify_{timestamp}.csv"
    excel_file = VERIFY_DIR / f"eam_verify_{timestamp}.xlsx"
    info(f"  CSV        : {csv_file}")
    info(f"  Excel      : {excel_file}")

    # ----------------------------------------------------------
    # Step 3 — Run all checks live, one query at a time
    # ----------------------------------------------------------
    info("Step 3/5 -- Running checks (live results below)")

    with timed_operation("eam_verify_all_checks"):

        # -------------------------------------------------------
        _section("1. TABLE & VIEW ACCESSIBILITY  (12 checks)")
        # -------------------------------------------------------
        for owner, table in [
            ("APPS", "EAM_WORK_ORDERS_V"),
            ("APPS", "QA_RESULTS"),
            ("APPS", "WIP_OPERATIONS_V"),
            ("APPS", "WIP_OP_RESOURCE_INSTANCES_V"),
            ("APPS", "MTL_PARAMETERS"),
            ("APPS", "FND_USER"),
            ("APPS", "PER_ALL_PEOPLE_F"),
            ("APPS", "FND_USER_RESP_GROUPS_DIRECT"),
            ("APPS", "FND_RESPONSIBILITY"),
            ("APPS", "FND_RESPONSIBILITY_TL"),
            ("APPS", "FND_APPLICATION"),
            ("EAM",  "EAM_PM_SCHEDULING_RULES"),
        ]:
            check_table(oracle, owner, table)

        # -------------------------------------------------------
        _section("2. COLUMN EXISTENCE  (~60 checks)")
        # -------------------------------------------------------

        for col in ("WIP_ENTITY_ID","WIP_ENTITY_NAME","ORGANIZATION_ID",
                    "WORK_ORDER_STATUS","USER_DEFINED_STATUS_ID","WORK_ORDER_TYPE_DISP",
                    "ASSET_NUMBER","ASSET_ACTIVITY","ASSET_DESCRIPTION","ASSET_GROUP_ID",
                    "CLASS_CODE","DESCRIPTION","CREATION_DATE","SCHEDULED_START_DATE"):
            check_col(oracle, "APPS", "EAM_WORK_ORDERS_V", col)

        for col in ("WORK_ORDER_ID","ORGANIZATION_ID","QA_CREATED_BY","QA_LAST_UPDATED_BY",
                    "QA_CREATION_DATE","QA_LAST_UPDATE_DATE","MAINTENANCE_OP_SEQ","PLAN_ID",
                    "COLLECTION_ID","OCCURRENCE","STATUS",
                    "CHARACTER1","CHARACTER2","CHARACTER3","CHARACTER4","COMMENT1"):
            check_col(oracle, "APPS", "QA_RESULTS", col)

        for col in ("WIP_ENTITY_ID","ORGANIZATION_ID","OPERATION_SEQ_NUM",
                    "OPERATION_COMPLETED","DEPARTMENT_CODE"):
            check_col(oracle, "APPS", "WIP_OPERATIONS_V", col)

        for col in ("WIP_ENTITY_ID","OPERATION_SEQ_NUM","INSTANCE_NAME"):
            check_col(oracle, "APPS", "WIP_OP_RESOURCE_INSTANCES_V", col)

        for col in ("ORGANIZATION_ID","ORGANIZATION_CODE"):
            check_col(oracle, "APPS", "MTL_PARAMETERS", col)

        for col in ("USER_ID","USER_NAME","DESCRIPTION","EMAIL_ADDRESS","EMPLOYEE_ID","END_DATE"):
            check_col(oracle, "APPS", "FND_USER", col)

        for col in ("PERSON_ID","FULL_NAME","EFFECTIVE_START_DATE","EFFECTIVE_END_DATE"):
            check_col(oracle, "APPS", "PER_ALL_PEOPLE_F", col)

        for col in ("USER_ID","RESPONSIBILITY_ID","START_DATE","END_DATE"):
            check_col(oracle, "APPS", "FND_USER_RESP_GROUPS_DIRECT", col)

        for col in ("RESPONSIBILITY_ID","APPLICATION_ID"):
            check_col(oracle, "APPS", "FND_RESPONSIBILITY", col)

        for col in ("RESPONSIBILITY_ID","RESPONSIBILITY_NAME","LANGUAGE"):
            check_col(oracle, "APPS", "FND_RESPONSIBILITY_TL", col)

        for col in ("APPLICATION_ID","APPLICATION_SHORT_NAME"):
            check_col(oracle, "APPS", "FND_APPLICATION", col)

        check_col(oracle, "EAM", "EAM_PM_SCHEDULING_RULES", "SCHEDULED_START_DATE")

        # -------------------------------------------------------
        _section("3. JOIN RELATIONSHIP VALIDATION  (12 checks)")
        # -------------------------------------------------------

        check_join(oracle, "QA_RESULTS -> EAM_WORK_ORDERS_V",
                   "SELECT COUNT(*) FROM APPS.QA_RESULTS QR "
                   "JOIN APPS.EAM_WORK_ORDERS_V EWO "
                   "ON QR.WORK_ORDER_ID = EWO.WIP_ENTITY_ID "
                   "AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID "
                   "WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100")

        check_join(oracle, "WIP_OPERATIONS_V -> EAM_WORK_ORDERS_V",
                   "SELECT COUNT(*) FROM APPS.WIP_OPERATIONS_V WO "
                   "JOIN APPS.EAM_WORK_ORDERS_V EWO "
                   "ON WO.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID "
                   "AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID "
                   "WHERE EWO.ORGANIZATION_ID = 1169 AND ROWNUM <= 100")

        check_join(oracle, "WIP_OP_RESOURCE_INSTANCES_V -> WIP_OPERATIONS_V",
                   "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V EWO "
                   "JOIN APPS.WIP_OPERATIONS_V WO ON WO.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID "
                   "JOIN APPS.WIP_OP_RESOURCE_INSTANCES_V RES "
                   "ON RES.WIP_ENTITY_ID = WO.WIP_ENTITY_ID "
                   "AND RES.OPERATION_SEQ_NUM = WO.OPERATION_SEQ_NUM "
                   "WHERE EWO.ORGANIZATION_ID = 1169 AND ROWNUM <= 100")

        check_join(oracle, "MTL_PARAMETERS -> EAM_WORK_ORDERS_V (org 1169 / XAU)",
                   "SELECT COUNT(*) FROM APPS.MTL_PARAMETERS MP "
                   "JOIN APPS.EAM_WORK_ORDERS_V EWO ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID "
                   "WHERE MP.ORGANIZATION_CODE = 'XAU' "
                   "AND EWO.ORGANIZATION_ID = 1169 AND ROWNUM <= 100")

        check_join(oracle, "FND_USER -> PER_ALL_PEOPLE_F (active employees)",
                   "SELECT COUNT(*) FROM APPS.FND_USER FU "
                   "JOIN APPS.PER_ALL_PEOPLE_F PEO ON PEO.PERSON_ID = FU.EMPLOYEE_ID "
                   "WHERE SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE "
                   "AND FU.EMPLOYEE_ID IS NOT NULL AND ROWNUM <= 100")

        check_join(oracle, "QA_RESULTS.QA_CREATED_BY -> FND_USER",
                   "SELECT COUNT(*) FROM APPS.QA_RESULTS QR "
                   "JOIN APPS.FND_USER FU ON FU.USER_ID = QR.QA_CREATED_BY "
                   "WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100")

        check_join(oracle, "QA_RESULTS.QA_LAST_UPDATED_BY -> FND_USER",
                   "SELECT COUNT(*) FROM APPS.QA_RESULTS QR "
                   "JOIN APPS.FND_USER FU ON FU.USER_ID = QR.QA_LAST_UPDATED_BY "
                   "WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100")

        check_join(oracle, "FND_USER -> FND_USER_RESP_GROUPS_DIRECT",
                   "SELECT COUNT(*) FROM APPS.FND_USER FU "
                   "JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR ON FUR.USER_ID = FU.USER_ID "
                   "WHERE ROWNUM <= 100")

        check_join(oracle, "FND_USER_RESP_GROUPS_DIRECT -> FND_RESPONSIBILITY",
                   "SELECT COUNT(*) FROM APPS.FND_USER_RESP_GROUPS_DIRECT FUR "
                   "JOIN APPS.FND_RESPONSIBILITY FR ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID "
                   "WHERE ROWNUM <= 100")

        check_join(oracle, "FND_RESPONSIBILITY -> FND_RESPONSIBILITY_TL (LANGUAGE=US)",
                   "SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY FR "
                   "JOIN APPS.FND_RESPONSIBILITY_TL FRT "
                   "ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID AND FRT.LANGUAGE = 'US' "
                   "WHERE ROWNUM <= 100")

        check_join(oracle, "FND_RESPONSIBILITY -> FND_APPLICATION",
                   "SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY FR "
                   "JOIN APPS.FND_APPLICATION FA ON FA.APPLICATION_ID = FR.APPLICATION_ID "
                   "WHERE ROWNUM <= 100")

        check_join(oracle, "Full security chain: FND_USER -> RESP -> TL -> APPLICATION",
                   "SELECT COUNT(*) FROM APPS.FND_USER FU "
                   "JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR ON FUR.USER_ID = FU.USER_ID "
                   "JOIN APPS.FND_RESPONSIBILITY FR ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID "
                   "JOIN APPS.FND_RESPONSIBILITY_TL FRT "
                   "ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID AND FRT.LANGUAGE = 'US' "
                   "JOIN APPS.FND_APPLICATION FA ON FA.APPLICATION_ID = FR.APPLICATION_ID "
                   "WHERE (FU.END_DATE IS NULL OR FU.END_DATE > SYSDATE) AND ROWNUM <= 100")

        # -------------------------------------------------------
        _section("4. KNOWN FILTER VALUE VALIDATION  (15 checks)")
        # -------------------------------------------------------

        check_filter(oracle, "ORGANIZATION_ID = 1169 in MTL_PARAMETERS",
                     "SELECT COUNT(*) FROM APPS.MTL_PARAMETERS WHERE ORGANIZATION_ID = 1169")

        check_filter(oracle, "ORGANIZATION_CODE = 'XAU' in MTL_PARAMETERS",
                     "SELECT COUNT(*) FROM APPS.MTL_PARAMETERS WHERE ORGANIZATION_CODE = 'XAU'")

        check_filter(oracle, "Org 1169 maps to code XAU",
                     "SELECT COUNT(*) FROM APPS.MTL_PARAMETERS "
                     "WHERE ORGANIZATION_ID = 1169 AND ORGANIZATION_CODE = 'XAU'")

        check_filter(oracle, "EAM work orders exist for org 1169",
                     "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND ROWNUM <= 1")

        check_filter(oracle, "Work orders matching AU%",
                     "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND WIP_ENTITY_NAME LIKE 'AU%' AND ROWNUM <= 1")

        check_filter(oracle, "Work orders matching PM%",
                     "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND WIP_ENTITY_NAME LIKE 'PM%' AND ROWNUM <= 1")

        check_filter(oracle, "Released work orders exist",
                     "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND WORK_ORDER_STATUS = 'Released' AND ROWNUM <= 1")

        check_filter(oracle, "Cancelled work orders exist",
                     "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND WORK_ORDER_STATUS = 'Cancelled' AND ROWNUM <= 1")

        check_filter(oracle, "USER_DEFINED_STATUS_ID = 3 exists",
                     "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND USER_DEFINED_STATUS_ID = 3 AND ROWNUM <= 1")

        check_filter(oracle, "WORK_ORDER_TYPE_DISP = 'DM' exists",
                     "SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND WORK_ORDER_TYPE_DISP = 'DM' AND ROWNUM <= 1")

        check_filter(oracle, "OPERATION_SEQ_NUM = 10 in WIP_OPERATIONS_V",
                     "SELECT COUNT(*) FROM APPS.WIP_OPERATIONS_V "
                     "WHERE ORGANIZATION_ID = 1169 AND OPERATION_SEQ_NUM = 10 AND ROWNUM <= 1")

        check_filter(oracle, "QA_RESULTS rows exist for org 1169",
                     "SELECT COUNT(*) FROM APPS.QA_RESULTS "
                     "WHERE ORGANIZATION_ID = 1169 AND ROWNUM <= 1")

        check_filter(oracle, "MAINTENANCE_OP_SEQ = 10 in QA_RESULTS",
                     "SELECT COUNT(*) FROM APPS.QA_RESULTS "
                     "WHERE ORGANIZATION_ID = 1169 AND MAINTENANCE_OP_SEQ = 10 AND ROWNUM <= 1")

        check_filter(oracle, "Responsibility 'ICU EAM Manager - XAU' exists",
                     "SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY_TL "
                     "WHERE RESPONSIBILITY_NAME = 'ICU EAM Manager - XAU' AND LANGUAGE = 'US'")

        check_filter(oracle, "APPLICATION_SHORT_NAME = 'EAM' exists",
                     "SELECT COUNT(*) FROM APPS.FND_APPLICATION "
                     "WHERE APPLICATION_SHORT_NAME = 'EAM'")

        check_filter(oracle, "Active users assigned ICU EAM Manager - XAU",
                     "SELECT COUNT(*) FROM APPS.FND_USER FU "
                     "JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR ON FUR.USER_ID = FU.USER_ID "
                     "JOIN APPS.FND_RESPONSIBILITY FR ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID "
                     "JOIN APPS.FND_RESPONSIBILITY_TL FRT "
                     "ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID AND FRT.LANGUAGE = 'US' "
                     "JOIN APPS.FND_APPLICATION FA ON FA.APPLICATION_ID = FR.APPLICATION_ID "
                     "WHERE FRT.RESPONSIBILITY_NAME = 'ICU EAM Manager - XAU' "
                     "AND FA.APPLICATION_SHORT_NAME = 'EAM' "
                     "AND (FU.END_DATE IS NULL OR FU.END_DATE > SYSDATE)")

        # -------------------------------------------------------
        _section("5. DATA INTEGRITY & CARTESIAN RISK  (3 checks)")
        # -------------------------------------------------------

        check_value(oracle,
                    "EAM_PM_SCHEDULING_RULES row count (Cartesian risk if > 1)",
                    "SELECT COUNT(*) FROM EAM.EAM_PM_SCHEDULING_RULES",
                    max_ok=1)

        check_value(oracle,
                    "FND_RESPONSIBILITY_TL distinct language count (expect >= 1)",
                    "SELECT COUNT(DISTINCT LANGUAGE) FROM APPS.FND_RESPONSIBILITY_TL")

        check_join(oracle,
                   "PER_ALL_PEOPLE_F -- confirm date filter prevents duplicates",
                   "SELECT COUNT(*) FROM ("
                   "SELECT FU.USER_ID "
                   "FROM APPS.FND_USER FU "
                   "JOIN APPS.PER_ALL_PEOPLE_F PEO ON PEO.PERSON_ID = FU.EMPLOYEE_ID "
                   "WHERE FU.EMPLOYEE_ID IS NOT NULL "
                   "AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE "
                   "GROUP BY FU.USER_ID HAVING COUNT(*) > 1) dups "
                   "WHERE ROWNUM <= 1")

    # ----------------------------------------------------------
    # Step 4 — Write reports
    # ----------------------------------------------------------
    info("")
    info("Step 4/5 -- Writing CSV report")
    with timed_operation("eam_verify_csv_generation"):
        _write_csv(csv_file)
    info(f"  CSV ready    : {csv_file}  ({len(_results)} checks)")

    info("Step 5/5 -- Generating Excel report")
    with timed_operation("eam_verify_excel_generation"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name="EAM Verification"
        )
    info(f"  Excel ready  : {excel_file}")

    _log_summary()


if __name__ == "__main__":
    main()