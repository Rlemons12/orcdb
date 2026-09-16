from __future__ import annotations

import csv
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configuration.config import OUTPUT_BASE_DIR, ensure_output_dirs
from configuration.orcdb_logger import error, info, set_request_id, timed_operation
from oracledb_connector import OracleDBConnector


OUTPUT_DIR = OUTPUT_BASE_DIR / "configured_asset_bom_discovery"
DELIM = "~|~"

KNOWN_TABLES = (
    ("APPS", "EAM_WORK_ORDERS_V"),
    ("BOM", "BOM_BILL_OF_MATERIALS"),
    ("BOM", "BOM_INVENTORY_COMPONENTS"),
    ("INV", "MTL_SYSTEM_ITEMS_B"),
    ("INV", "MTL_EAM_ASSET_NUMBERS"),
    ("CSI", "CSI_ITEM_INSTANCES"),
)


def sql_text(value: str) -> str:
    return value.replace("'", "''")


def run_delimited(
    oracle: OracleDBConnector,
    sql: str,
    columns: list[str],
) -> list[dict[str, str]]:
    ok, out = oracle.run_query(sql)
    if not ok or "ORA-" in out or "SP2-" in out:
        raise RuntimeError(out)

    rows: list[dict[str, str]] = []
    for line in out.splitlines():
        line = line.strip()
        if not line or DELIM not in line:
            continue
        values = line.split(DELIM)
        values += [""] * (len(columns) - len(values))
        rows.append(dict(zip(columns, values[: len(columns)])))
    return rows


def write_csv(path: Path, rows: list[dict[str, str]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    info(f"Wrote {path} ({len(rows)} rows)")


def scalar_count(oracle: OracleDBConnector, sql: str) -> tuple[str, str]:
    ok, out = oracle.run_query(sql)
    if not ok or "ORA-" in out or "SP2-" in out:
        return "ERROR", out.replace("\n", " ")[:500]
    return "OK", out.strip()


def object_exists(oracle: OracleDBConnector, owner: str, table_name: str) -> bool:
    status, count = scalar_count(
        oracle,
        f"""
        SELECT COUNT(*)
        FROM ALL_OBJECTS
        WHERE OWNER = '{sql_text(owner)}'
          AND OBJECT_NAME = '{sql_text(table_name)}'
          AND OBJECT_TYPE IN ('TABLE', 'VIEW', 'SYNONYM')
        """,
    )
    return status == "OK" and count not in ("", "0")


def column_exists(oracle: OracleDBConnector, owner: str, table_name: str, column: str) -> bool:
    status, count = scalar_count(
        oracle,
        f"""
        SELECT COUNT(*)
        FROM ALL_TAB_COLUMNS
        WHERE OWNER = '{sql_text(owner)}'
          AND TABLE_NAME = '{sql_text(table_name)}'
          AND COLUMN_NAME = '{sql_text(column)}'
        """,
    )
    return status == "OK" and count not in ("", "0")


def discover_objects(oracle: OracleDBConnector) -> list[dict[str, str]]:
    columns = ["OWNER", "OBJECT_NAME", "OBJECT_TYPE", "STATUS"]
    expr = f"OWNER || '{DELIM}' || OBJECT_NAME || '{DELIM}' || OBJECT_TYPE || '{DELIM}' || NVL(STATUS, '')"
    return run_delimited(
        oracle,
        f"""
        SELECT {expr}
        FROM ALL_OBJECTS
        WHERE OWNER IN ('APPS', 'EAM', 'BOM', 'INV', 'CSI')
          AND OBJECT_NAME IN (
              'EAM_WORK_ORDERS_V',
              'BOM_BILL_OF_MATERIALS',
              'BOM_INVENTORY_COMPONENTS',
              'MTL_SYSTEM_ITEMS_B',
              'MTL_EAM_ASSET_NUMBERS',
              'CSI_ITEM_INSTANCES'
          )
        ORDER BY OWNER, OBJECT_TYPE, OBJECT_NAME
        """,
        columns,
    )


def discover_synonyms(oracle: OracleDBConnector) -> list[dict[str, str]]:
    columns = ["OWNER", "SYNONYM_NAME", "TABLE_OWNER", "TABLE_NAME"]
    expr = (
        f"OWNER || '{DELIM}' || SYNONYM_NAME || '{DELIM}' || "
        f"TABLE_OWNER || '{DELIM}' || TABLE_NAME"
    )
    return run_delimited(
        oracle,
        f"""
        SELECT {expr}
        FROM ALL_SYNONYMS
        WHERE OWNER IN ('APPS', 'PUBLIC')
          AND SYNONYM_NAME IN (
              'EAM_WORK_ORDERS_V',
              'BOM_BILL_OF_MATERIALS',
              'BOM_INVENTORY_COMPONENTS',
              'MTL_SYSTEM_ITEMS_B',
              'MTL_EAM_ASSET_NUMBERS',
              'CSI_ITEM_INSTANCES'
          )
        ORDER BY OWNER, SYNONYM_NAME
        """,
        columns,
    )


def discover_columns(oracle: OracleDBConnector) -> list[dict[str, str]]:
    columns = ["OWNER", "TABLE_NAME", "COLUMN_ID", "COLUMN_NAME", "DATA_TYPE", "NULLABLE"]
    expr = (
        f"OWNER || '{DELIM}' || TABLE_NAME || '{DELIM}' || TO_CHAR(COLUMN_ID) || '{DELIM}' || "
        f"COLUMN_NAME || '{DELIM}' || DATA_TYPE || '{DELIM}' || NULLABLE"
    )
    return run_delimited(
        oracle,
        f"""
        SELECT {expr}
        FROM ALL_TAB_COLUMNS
        WHERE OWNER IN ('APPS', 'EAM', 'BOM', 'INV', 'CSI')
          AND TABLE_NAME IN (
              'EAM_WORK_ORDERS_V',
              'BOM_BILL_OF_MATERIALS',
              'BOM_INVENTORY_COMPONENTS',
              'MTL_SYSTEM_ITEMS_B',
              'MTL_EAM_ASSET_NUMBERS',
              'CSI_ITEM_INSTANCES'
          )
        ORDER BY OWNER, TABLE_NAME, COLUMN_ID
        """,
        columns,
    )


def discover_fks(oracle: OracleDBConnector) -> list[dict[str, str]]:
    columns = [
        "CONSTRAINT_NAME",
        "CHILD_OWNER",
        "CHILD_TABLE",
        "CHILD_COLUMN",
        "PARENT_OWNER",
        "PARENT_TABLE",
        "PARENT_COLUMN",
    ]
    expr = (
        f"AC.CONSTRAINT_NAME || '{DELIM}' || AC.OWNER || '{DELIM}' || AC.TABLE_NAME || '{DELIM}' || "
        f"ACC.COLUMN_NAME || '{DELIM}' || ARC.OWNER || '{DELIM}' || ARC.TABLE_NAME || '{DELIM}' || ARCC.COLUMN_NAME"
    )
    return run_delimited(
        oracle,
        f"""
        SELECT {expr}
        FROM ALL_CONSTRAINTS AC
        JOIN ALL_CONS_COLUMNS ACC
          ON ACC.OWNER = AC.OWNER
         AND ACC.CONSTRAINT_NAME = AC.CONSTRAINT_NAME
        JOIN ALL_CONSTRAINTS ARC
          ON ARC.OWNER = AC.R_OWNER
         AND ARC.CONSTRAINT_NAME = AC.R_CONSTRAINT_NAME
        JOIN ALL_CONS_COLUMNS ARCC
          ON ARCC.OWNER = ARC.OWNER
         AND ARCC.CONSTRAINT_NAME = ARC.CONSTRAINT_NAME
         AND ARCC.POSITION = ACC.POSITION
        WHERE AC.CONSTRAINT_TYPE = 'R'
          AND AC.OWNER IN ('EAM', 'BOM', 'INV', 'CSI')
          AND (
              AC.TABLE_NAME IN (
                  'BOM_BILL_OF_MATERIALS',
                  'BOM_INVENTORY_COMPONENTS',
                  'MTL_SYSTEM_ITEMS_B',
                  'MTL_EAM_ASSET_NUMBERS',
                  'CSI_ITEM_INSTANCES'
              )
              OR ARC.TABLE_NAME IN (
                  'BOM_BILL_OF_MATERIALS',
                  'BOM_INVENTORY_COMPONENTS',
                  'MTL_SYSTEM_ITEMS_B',
                  'MTL_EAM_ASSET_NUMBERS',
                  'CSI_ITEM_INSTANCES'
              )
          )
        ORDER BY AC.OWNER, AC.TABLE_NAME, AC.CONSTRAINT_NAME, ACC.POSITION
        """,
        columns,
    )


def run_probe(oracle: OracleDBConnector, probe_name: str, sql: str) -> dict[str, str]:
    status, result = scalar_count(oracle, sql)
    return {"PROBE": probe_name, "STATUS": status, "RESULT": result}


def discover_join_probes(oracle: OracleDBConnector) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []

    rows.append(
        run_probe(
            oracle,
            "EWO.ASSET_GROUP_ID -> MSI.INVENTORY_ITEM_ID",
            """
            SELECT COUNT(*)
            FROM APPS.EAM_WORK_ORDERS_V EWO
            JOIN INV.MTL_SYSTEM_ITEMS_B MSI
              ON MSI.INVENTORY_ITEM_ID = EWO.ASSET_GROUP_ID
             AND MSI.ORGANIZATION_ID = EWO.ORGANIZATION_ID
            WHERE EWO.ORGANIZATION_ID = 1169
              AND EWO.ASSET_GROUP_ID IS NOT NULL
              AND ROWNUM <= 100
            """,
        )
    )

    rows.append(
        run_probe(
            oracle,
            "EWO.ASSET_GROUP_ID -> BOM header",
            """
            SELECT COUNT(*)
            FROM APPS.EAM_WORK_ORDERS_V EWO
            JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
              ON BBOM.ASSEMBLY_ITEM_ID = EWO.ASSET_GROUP_ID
             AND BBOM.ORGANIZATION_ID = EWO.ORGANIZATION_ID
            WHERE EWO.ORGANIZATION_ID = 1169
              AND EWO.ASSET_NUMBER IS NOT NULL
              AND ROWNUM <= 100
            """,
        )
    )

    rows.append(
        run_probe(
            oracle,
            "EWO.ASSET_GROUP_ID -> BOM components",
            """
            SELECT COUNT(*)
            FROM APPS.EAM_WORK_ORDERS_V EWO
            JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
              ON BBOM.ASSEMBLY_ITEM_ID = EWO.ASSET_GROUP_ID
             AND BBOM.ORGANIZATION_ID = EWO.ORGANIZATION_ID
            JOIN APPS.BOM_INVENTORY_COMPONENTS BIC
              ON BIC.BILL_SEQUENCE_ID = BBOM.BILL_SEQUENCE_ID
            WHERE EWO.ORGANIZATION_ID = 1169
              AND EWO.ASSET_NUMBER IS NOT NULL
              AND ROWNUM <= 100
            """,
        )
    )

    if object_exists(oracle, "INV", "MTL_EAM_ASSET_NUMBERS"):
        asset_col = "ASSET_NUMBER" if column_exists(oracle, "INV", "MTL_EAM_ASSET_NUMBERS", "ASSET_NUMBER") else None
        group_col = "ASSET_GROUP_ID" if column_exists(oracle, "INV", "MTL_EAM_ASSET_NUMBERS", "ASSET_GROUP_ID") else None
        org_col = "ORGANIZATION_ID" if column_exists(oracle, "INV", "MTL_EAM_ASSET_NUMBERS", "ORGANIZATION_ID") else None
        if asset_col and group_col and org_col:
            rows.append(
                run_probe(
                    oracle,
                    "MTL_EAM_ASSET_NUMBERS asset group -> BOM components",
                    f"""
                    SELECT COUNT(*)
                    FROM INV.MTL_EAM_ASSET_NUMBERS MEAN
                    JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
                      ON BBOM.ASSEMBLY_ITEM_ID = MEAN.{group_col}
                     AND BBOM.ORGANIZATION_ID = MEAN.{org_col}
                    JOIN APPS.BOM_INVENTORY_COMPONENTS BIC
                      ON BIC.BILL_SEQUENCE_ID = BBOM.BILL_SEQUENCE_ID
                    WHERE MEAN.{org_col} = 1169
                      AND MEAN.{asset_col} IS NOT NULL
                      AND ROWNUM <= 100
                    """,
                )
            )

    return rows


def discover_sample_configured_bom(oracle: OracleDBConnector) -> list[dict[str, str]]:
    columns = [
        "ASSET_NUMBER",
        "ASSET_DESCRIPTION",
        "ASSET_GROUP_ITEM",
        "ASSET_GROUP_DESCRIPTION",
        "BILL_SEQUENCE_ID",
        "ALTERNATE_BOM_DESIGNATOR",
        "COMPONENT_ITEM_ID",
        "PART_NUMBER",
        "PART_DESCRIPTION",
        "COMPONENT_QUANTITY",
        "COMPONENT_UOM",
        "EFFECTIVITY_DATE",
        "DISABLE_DATE",
    ]
    expr = " || '{0}' || ".format(DELIM).join(
        [
            "EWO.ASSET_NUMBER",
            "NVL(EWO.ASSET_DESCRIPTION, '')",
            "NVL(AG.SEGMENT1, '')",
            "NVL(AG.DESCRIPTION, '')",
            "TO_CHAR(BBOM.BILL_SEQUENCE_ID)",
            "NVL(BBOM.ALTERNATE_BOM_DESIGNATOR, '')",
            "TO_CHAR(BIC.COMPONENT_ITEM_ID)",
            "NVL(COMP.SEGMENT1, '')",
            "NVL(COMP.DESCRIPTION, '')",
            "TO_CHAR(BIC.COMPONENT_QUANTITY)",
            "NVL(COMP.PRIMARY_UOM_CODE, '')",
            "TO_CHAR(BIC.EFFECTIVITY_DATE, 'YYYY-MM-DD')",
            "TO_CHAR(BIC.DISABLE_DATE, 'YYYY-MM-DD')",
        ]
    )
    return run_delimited(
        oracle,
        f"""
        SELECT {expr}
        FROM APPS.EAM_WORK_ORDERS_V EWO
        JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
          ON BBOM.ASSEMBLY_ITEM_ID = EWO.ASSET_GROUP_ID
         AND BBOM.ORGANIZATION_ID = EWO.ORGANIZATION_ID
        JOIN APPS.BOM_INVENTORY_COMPONENTS BIC
          ON BIC.BILL_SEQUENCE_ID = BBOM.BILL_SEQUENCE_ID
        LEFT JOIN INV.MTL_SYSTEM_ITEMS_B AG
          ON AG.INVENTORY_ITEM_ID = EWO.ASSET_GROUP_ID
         AND AG.ORGANIZATION_ID = EWO.ORGANIZATION_ID
        LEFT JOIN INV.MTL_SYSTEM_ITEMS_B COMP
          ON COMP.INVENTORY_ITEM_ID = BIC.COMPONENT_ITEM_ID
         AND COMP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
        WHERE EWO.ORGANIZATION_ID = 1169
          AND EWO.ASSET_NUMBER IS NOT NULL
          AND ROWNUM <= 200
        ORDER BY EWO.ASSET_NUMBER, COMP.SEGMENT1
        """,
        columns,
    )


def main() -> None:
    set_request_id()
    ensure_output_dirs()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    oracle = OracleDBConnector()

    info("Configured asset BOM discovery starting")

    with timed_operation("configured_bom_metadata_discovery"):
        object_rows = discover_objects(oracle)
        synonym_rows = discover_synonyms(oracle)
        column_rows = discover_columns(oracle)
        fk_rows = discover_fks(oracle)
        probe_rows = discover_join_probes(oracle)
        sample_rows = discover_sample_configured_bom(oracle)

    write_csv(OUTPUT_DIR / f"object_candidates_{timestamp}.csv", object_rows, ["OWNER", "OBJECT_NAME", "OBJECT_TYPE", "STATUS"])
    write_csv(OUTPUT_DIR / f"synonym_candidates_{timestamp}.csv", synonym_rows, ["OWNER", "SYNONYM_NAME", "TABLE_OWNER", "TABLE_NAME"])
    write_csv(OUTPUT_DIR / f"column_candidates_{timestamp}.csv", column_rows, ["OWNER", "TABLE_NAME", "COLUMN_ID", "COLUMN_NAME", "DATA_TYPE", "NULLABLE"])
    write_csv(OUTPUT_DIR / f"fk_candidates_{timestamp}.csv", fk_rows, ["CONSTRAINT_NAME", "CHILD_OWNER", "CHILD_TABLE", "CHILD_COLUMN", "PARENT_OWNER", "PARENT_TABLE", "PARENT_COLUMN"])
    write_csv(OUTPUT_DIR / f"join_probes_{timestamp}.csv", probe_rows, ["PROBE", "STATUS", "RESULT"])
    write_csv(OUTPUT_DIR / f"sample_configured_bom_{timestamp}.csv", sample_rows, [
        "ASSET_NUMBER",
        "ASSET_DESCRIPTION",
        "ASSET_GROUP_ITEM",
        "ASSET_GROUP_DESCRIPTION",
        "BILL_SEQUENCE_ID",
        "ALTERNATE_BOM_DESIGNATOR",
        "COMPONENT_ITEM_ID",
        "PART_NUMBER",
        "PART_DESCRIPTION",
        "COMPONENT_QUANTITY",
        "COMPONENT_UOM",
        "EFFECTIVITY_DATE",
        "DISABLE_DATE",
    ])

    for row in probe_rows:
        info(f"{row['PROBE']}: {row['STATUS']} {row['RESULT']}")

    info(f"Configured asset BOM discovery complete: {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        error(str(exc))
        raise
