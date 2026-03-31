import sys
from pathlib import Path

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


DISCOVER_DIR = OUTPUT_BASE_DIR / "eam_fk_discovery"

# ===========================================================
#  Known base tables (resolved from APPS synonyms in
#  the verification run). Views are excluded — Oracle does
#  not define FK constraints on views.
# ===========================================================
KNOWN_TABLES = [
    # (base_owner, base_table, apps_alias)
    ("QA",       "QA_RESULTS",                    "APPS.QA_RESULTS"),
    ("INV",      "MTL_PARAMETERS",                "APPS.MTL_PARAMETERS"),
    ("APPLSYS",  "FND_USER",                      "APPS.FND_USER"),
    ("HR",       "PER_ALL_PEOPLE_F",              "APPS.PER_ALL_PEOPLE_F"),
    ("EAM",      "EAM_PM_SCHEDULING_RULES",       "EAM.EAM_PM_SCHEDULING_RULES"),
    ("APPLSYS",  "FND_USER_RESP_GROUPS_DIRECT",   "APPS.FND_USER_RESP_GROUPS_DIRECT"),
    ("APPLSYS",  "FND_RESPONSIBILITY",             "APPS.FND_RESPONSIBILITY"),
    ("APPLSYS",  "FND_RESPONSIBILITY_TL",          "APPS.FND_RESPONSIBILITY_TL"),
    ("APPLSYS",  "FND_APPLICATION",               "APPS.FND_APPLICATION"),
    # WIP tables — base owner is WIP schema in EBS
    ("WIP",      "WIP_OPERATIONS",               "APPS.WIP_OPERATIONS_V"),
    ("WIP",      "WIP_OP_RESOURCE_INSTANCES",    "APPS.WIP_OP_RESOURCE_INSTANCES_V"),
    # EAM work orders — base table behind the view
    ("EAM",      "WIP_DISCRETE_JOBS",            "APPS.EAM_WORK_ORDERS_V"),
    # Discovered layer 1 — FK from PER_ALL_PEOPLE_F.BUSINESS_GROUP_ID
    ("HR",       "HR_ALL_ORGANIZATION_UNITS",    "APPS.HR_ALL_ORGANIZATION_UNITS"),
]

# ===========================================================
#  Schemas to scope the inbound FK scan.
#  Only tables in these schemas will be checked as potential
#  children — prevents a full-database scan.
# ===========================================================
KNOWN_SCHEMAS = ("APPS", "QA", "INV", "APPLSYS", "HR", "EAM", "WIP")

# Accumulates all discovered relationships
_fk_rows:      list[dict] = []
_column_rows:  list[dict] = []
_summary_rows: list[dict] = []


# ===========================================================
#  Discovery functions
# ===========================================================

def discover_outbound_fks(oracle: OracleDBConnector,
                          owner: str, table: str, alias: str) -> None:
    """
    Find FK constraints ON this table — i.e. columns in this table
    that reference a parent table (outbound / child-side FKs).
    """
    info(f"    Outbound FKs from {alias} ({owner}.{table})")

    sql = (
        f"SELECT "
        f"  ac.constraint_name, "
        f"  ac.table_name        AS child_table, "
        f"  ac.owner             AS child_owner, "
        f"  acc.column_name      AS child_column, "
        f"  ac.r_owner           AS parent_owner, "
        f"  arc.table_name       AS parent_table, "
        f"  arcc.column_name     AS parent_column "
        f"FROM all_constraints ac "
        f"JOIN all_cons_columns acc "
        f"  ON acc.constraint_name = ac.constraint_name "
        f"  AND acc.owner = ac.owner "
        f"JOIN all_constraints arc "
        f"  ON arc.constraint_name = ac.r_constraint_name "
        f"  AND arc.owner = ac.r_owner "
        f"JOIN all_cons_columns arcc "
        f"  ON arcc.constraint_name = arc.constraint_name "
        f"  AND arcc.owner = arc.owner "
        f"  AND arcc.position = acc.position "
        f"WHERE ac.constraint_type = 'R' "
        f"  AND ac.owner = '{owner}' "
        f"  AND ac.table_name = '{table}' "
        f"ORDER BY ac.constraint_name, acc.position"
    )

    ok, out = oracle.run_query(sql)
    if not ok:
        error(f"      Query error: {out}")
        return

    rows = _parse_table_output(out)
    if not rows:
        info(f"      No outbound FKs found")
        return

    info(f"      Found {len(rows)} FK column mapping(s)")
    for row in rows:
        info(f"      -> {row[3]} references {row[4]}.{row[5]}.{row[6]}  [{row[0]}]")
        _fk_rows.append({
            "direction":        "OUTBOUND (child)",
            "known_table_alias": alias,
            "constraint_name":  row[0],
            "child_owner":      row[2],
            "child_table":      row[1],
            "child_column":     row[3],
            "parent_owner":     row[4],
            "parent_table":     row[5],
            "parent_column":    row[6],
        })


def discover_inbound_fks(oracle: OracleDBConnector,
                         owner: str, table: str, alias: str) -> None:
    """
    Find FK constraints that REFERENCE this table — i.e. other tables
    that have a FK pointing at this table (inbound / parent-side).
    Scoped to KNOWN_SCHEMAS only to avoid a full-database scan.
    """
    info(f"    Inbound FKs into {alias} ({owner}.{table})")

    # Build IN clause for known schemas
    schema_list = ", ".join(f"'{s}'" for s in KNOWN_SCHEMAS)

    sql = (
        f"SELECT "
        f"  ac.constraint_name, "
        f"  ac.table_name        AS child_table, "
        f"  ac.owner             AS child_owner, "
        f"  acc.column_name      AS child_column, "
        f"  arc.owner            AS parent_owner, "
        f"  arc.table_name       AS parent_table, "
        f"  arcc.column_name     AS parent_column "
        f"FROM all_constraints ac "
        f"JOIN all_cons_columns acc "
        f"  ON acc.constraint_name = ac.constraint_name "
        f"  AND acc.owner = ac.owner "
        f"JOIN all_constraints arc "
        f"  ON arc.constraint_name = ac.r_constraint_name "
        f"  AND arc.owner = ac.r_owner "
        f"JOIN all_cons_columns arcc "
        f"  ON arcc.constraint_name = arc.constraint_name "
        f"  AND arcc.owner = arc.owner "
        f"  AND arcc.position = acc.position "
        f"WHERE ac.constraint_type = 'R' "
        f"  AND ac.owner IN ({schema_list}) "
        f"  AND arc.owner = '{owner}' "
        f"  AND arc.table_name = '{table}' "
        f"ORDER BY ac.owner, ac.table_name, ac.constraint_name, acc.position"
    )

    ok, out = oracle.run_query(sql)
    if not ok:
        error(f"      Query error: {out}")
        return

    rows = _parse_table_output(out)
    if not rows:
        info(f"      No inbound FKs found")
        return

    info(f"      Found {len(rows)} FK column mapping(s)")
    seen_tables = set()
    for row in rows:
        child_label = f"{row[2]}.{row[1]}"
        if child_label not in seen_tables:
            info(f"      <- {child_label}.{row[3]} references this table  [{row[0]}]")
            seen_tables.add(child_label)
        _fk_rows.append({
            "direction":         "INBOUND (parent)",
            "known_table_alias": alias,
            "constraint_name":   row[0],
            "child_owner":       row[2],
            "child_table":       row[1],
            "child_column":      row[3],
            "parent_owner":      row[4],
            "parent_table":      row[5],
            "parent_column":     row[6],
        })


def discover_columns_for_new_tables(oracle: OracleDBConnector) -> None:
    """
    For every new (non-known) table discovered via FK relationships
    that lives in a known schema, fetch its column list.
    """
    known_bases = {(r[0], r[1]) for r in KNOWN_TABLES}

    # Only document tables within our known schemas
    new_tables = set()
    for row in _fk_rows:
        key = (row["child_owner"], row["child_table"])
        if key not in known_bases and row["child_owner"] in KNOWN_SCHEMAS:
            new_tables.add(key)

    if not new_tables:
        info("  No new tables to document")
        return

    info(f"  Fetching columns for {len(new_tables)} newly discovered table(s)...")

    for owner, table in sorted(new_tables):
        info(f"    Columns of {owner}.{table}")

        sql = (
            f"SELECT column_name, data_type, nullable "
            f"FROM all_tab_columns "
            f"WHERE owner = '{owner}' AND table_name = '{table}' "
            f"ORDER BY column_id"
        )
        ok, out = oracle.run_query(sql)
        if not ok or not out.strip():
            info(f"      (no columns found or access denied)")
            continue

        for line in out.strip().splitlines():
            parts = line.split()
            if len(parts) >= 2:
                col_name  = parts[0]
                data_type = parts[1]
                nullable  = parts[2] if len(parts) >= 3 else "?"
                _column_rows.append({
                    "table_owner": owner,
                    "table_name":  table,
                    "column_name": col_name,
                    "data_type":   data_type,
                    "nullable":    nullable,
                })
                info(f"      {col_name}  {data_type}  nullable={nullable}")


def build_summary() -> None:
    """Summarise discovered relationships per known table."""
    info("  Building summary...")

    counts: dict[str, dict] = {}
    for row in _fk_rows:
        alias = row["known_table_alias"]
        if alias not in counts:
            counts[alias] = {"inbound": 0, "outbound": 0, "inbound_tables": set(),
                             "outbound_tables": set()}
        if row["direction"].startswith("INBOUND"):
            counts[alias]["inbound"] += 1
            counts[alias]["inbound_tables"].add(
                f"{row['child_owner']}.{row['child_table']}")
        else:
            counts[alias]["outbound"] += 1
            counts[alias]["outbound_tables"].add(
                f"{row['parent_owner']}.{row['parent_table']}")

    for alias, c in sorted(counts.items()):
        _summary_rows.append({
            "table":                    alias,
            "inbound_fk_columns":       c["inbound"],
            "inbound_referencing_tables": len(c["inbound_tables"]),
            "outbound_fk_columns":      c["outbound"],
            "outbound_referenced_tables": len(c["outbound_tables"]),
            "referencing_tables":       ", ".join(sorted(c["inbound_tables"])),
            "referenced_tables":        ", ".join(sorted(c["outbound_tables"])),
        })
        info(f"    {alias}: "
             f"{c['inbound']} inbound FK cols from "
             f"{len(c['inbound_tables'])} table(s), "
             f"{c['outbound']} outbound FK cols to "
             f"{len(c['outbound_tables'])} table(s)")


# ===========================================================
#  Helpers
# ===========================================================

def _parse_table_output(out: str) -> list[list[str]]:
    """
    Parse multi-column SQLcl output (space-separated) into rows.
    Skips blank lines.
    """
    rows = []
    for line in out.strip().splitlines():
        line = line.strip()
        if line:
            rows.append(line.split())
    return rows


def _write_csv(rows: list[dict], path: Path) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


# ===========================================================
#  Main
# ===========================================================

def main():
    set_request_id()
    info("=" * 56)
    info("EAM FK Relationship Discovery -- Starting")
    info("=" * 56)

    info("Step 1/6 -- Initializing directories")
    ensure_output_dirs()
    DISCOVER_DIR.mkdir(parents=True, exist_ok=True)
    info(f"  Output dir : {DISCOVER_DIR}")

    info("Step 2/6 -- Connecting to Oracle")
    oracle = OracleDBConnector()
    info("  Connector ready")

    timestamp        = datetime.now().strftime("%Y%m%d_%H%M%S")
    fk_csv           = DISCOVER_DIR / f"fk_relationships_{timestamp}.csv"
    fk_excel         = DISCOVER_DIR / f"fk_relationships_{timestamp}.xlsx"
    col_csv          = DISCOVER_DIR / f"new_table_columns_{timestamp}.csv"
    col_excel        = DISCOVER_DIR / f"new_table_columns_{timestamp}.xlsx"
    summary_csv      = DISCOVER_DIR / f"fk_summary_{timestamp}.csv"
    summary_excel    = DISCOVER_DIR / f"fk_summary_{timestamp}.xlsx"

    info(f"  FK map     : {fk_excel}")
    info(f"  New cols   : {col_excel}")
    info(f"  Summary    : {summary_excel}")

    # ----------------------------------------------------------
    # Step 3 — Discover outbound FKs (what our tables reference)
    # ----------------------------------------------------------
    info("Step 3/6 -- Discovering outbound FKs (our tables -> parent tables)")
    info(f"  Checking {len(KNOWN_TABLES)} known tables...")

    with timed_operation("fk_outbound_discovery"):
        for owner, table, alias in KNOWN_TABLES:
            info("")
            discover_outbound_fks(oracle, owner, table, alias)

    info(f"  Outbound discovery complete -- {len(_fk_rows)} FK column mapping(s) found")

    # ----------------------------------------------------------
    # Step 4 — Discover inbound FKs (what references our tables)
    # ----------------------------------------------------------
    info("Step 4/6 -- Discovering inbound FKs (other tables -> our tables)")
    info("  This may take longer -- scanning all_constraints across full schema...")

    pre_count = len(_fk_rows)
    with timed_operation("fk_inbound_discovery"):
        for owner, table, alias in KNOWN_TABLES:
            info("")
            discover_inbound_fks(oracle, owner, table, alias)

    new_inbound = len(_fk_rows) - pre_count
    info(f"  Inbound discovery complete -- {new_inbound} additional FK column mapping(s) found")

    # ----------------------------------------------------------
    # Step 5 — Fetch columns for newly discovered tables
    # ----------------------------------------------------------
    info("Step 5/6 -- Fetching columns for newly discovered tables")
    with timed_operation("fk_column_discovery"):
        discover_columns_for_new_tables(oracle)

    info(f"  Column discovery complete -- {len(_column_rows)} column(s) documented")

    # ----------------------------------------------------------
    # Step 6 — Build summary and write all reports
    # ----------------------------------------------------------
    info("Step 6/6 -- Building summary and writing reports")

    build_summary()

    # FK relationships
    _write_csv(_fk_rows, fk_csv)
    ReportUtility.csv_to_excel(
        csv_path=fk_csv,
        excel_path=fk_excel,
        sheet_name="FK Relationships"
    )
    info(f"  FK map written     : {fk_excel}  ({len(_fk_rows)} rows)")

    # New table columns
    if _column_rows:
        _write_csv(_column_rows, col_csv)
        ReportUtility.csv_to_excel(
            csv_path=col_csv,
            excel_path=col_excel,
            sheet_name="New Table Columns"
        )
        info(f"  New cols written   : {col_excel}  ({len(_column_rows)} rows)")
    else:
        info("  No new table columns to write")

    # Summary
    if _summary_rows:
        _write_csv(_summary_rows, summary_csv)
        ReportUtility.csv_to_excel(
            csv_path=summary_csv,
            excel_path=summary_excel,
            sheet_name="FK Summary"
        )
        info(f"  Summary written    : {summary_excel}  ({len(_summary_rows)} rows)")

    # Final totals
    known_set = {(r[0], r[1]) for r in KNOWN_TABLES}
    new_tables = {(r["child_owner"], r["child_table"])
                  for r in _fk_rows
                  if (r["child_owner"], r["child_table"]) not in known_set}

    info("")
    info("=" * 56)
    info(f"  DISCOVERY COMPLETE")
    info(f"  Known tables scanned      : {len(KNOWN_TABLES)}")
    info(f"  Total FK column mappings  : {len(_fk_rows)}")
    info(f"  New tables discovered     : {len(new_tables)}")
    info(f"  New table columns fetched : {len(_column_rows)}")
    info("=" * 56)


if __name__ == "__main__":
    main()