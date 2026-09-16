"""Read-only Oracle extract for the agreed preliminary Lifecare asset scope."""
import csv
import io
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from oracledb_connector import OracleDBConnector

OUT = ROOT / 'outputs/lifecare_mtbf_12_months'
OUT.mkdir(exist_ok=True)

def query(name, sql):
    (OUT / (name + '.sql')).write_text(sql, encoding='utf-8')
    c = OracleDBConnector()
    preamble = 'SET SQLFORMAT CSV\nSET FEEDBACK OFF\nSET HEADING ON\nSET PAGESIZE 50000\nSET LINESIZE 32767\nSET DEFINE OFF\n'
    result = subprocess.run([c.sqlcl_path, '-S', c.connect_string], input=preamble + sql + '\nEXIT\n', capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    if result.returncode or re.search(r'ORA-\d+|SP2-\d+', result.stdout + result.stderr):
        raise RuntimeError('Oracle query failed: ' + (result.stdout + result.stderr)[:1500])
    text = result.stdout.strip()
    (OUT / (name + '.csv')).write_text(text + '\n', encoding='utf-8-sig')
    return list(csv.DictReader(io.StringIO(text)))

if __name__ == '__main__':
    with (ROOT / 'outputs/lifecare_mtbf_assets/lifecare_asset_review_20260909.csv').open(encoding='utf-8-sig') as f:
        assets = list(csv.DictReader(f))
    numbers = sorted({a['Asset Number'] for a in assets})
    literals = ','.join("'" + n.replace("'", "''") + "'" for n in numbers)
    sql = f"""SELECT E.WIP_ENTITY_ID, E.WIP_ENTITY_NAME WORK_ORDER, E.ASSET_NUMBER,
 E.ASSET_DESCRIPTION, E.WORK_ORDER_TYPE_DISP WO_TYPE, E.WORK_ORDER_STATUS,
 E.STATUS_TYPE, E.DESCRIPTION WO_DESCRIPTION, E.ASSET_GROUP_ID,
 E.OWNING_DEPARTMENT_CODE, E.PARENT_WIP_ENTITY_ID,
 TO_CHAR(E.CREATION_DATE,'YYYY-MM-DD HH24:MI:SS') CREATED_DATE,
 TO_CHAR(E.ACTUAL_START_DATE,'YYYY-MM-DD HH24:MI:SS') ACTUAL_START_DATE,
 TO_CHAR(E.DATE_COMPLETED,'YYYY-MM-DD HH24:MI:SS') COMPLETED_DATE,
 E.FAILURE_ID, E.FAILURE_ENTRY_ID, E.FAILURE_CODE, E.CAUSE_CODE,
 E.RESOLUTION_CODE, TO_CHAR(E.FAILURE_DATE,'YYYY-MM-DD HH24:MI:SS') FAILURE_DATE,
 E.SHUTDOWN_TYPE_DISP, E.ACTIVITY_CAUSE_DISP
FROM APPS.EAM_WORK_ORDERS_V E
WHERE E.ORGANIZATION_ID=1169 AND E.ASSET_NUMBER IN ({literals})
AND ((E.CREATION_DATE >= DATE '2025-09-09' AND E.CREATION_DATE < DATE '2026-09-09')
 OR (E.FAILURE_DATE >= DATE '2025-09-09' AND E.FAILURE_DATE < DATE '2026-09-09'))
ORDER BY E.ASSET_NUMBER,E.CREATION_DATE,E.WIP_ENTITY_ID;"""
    rows = query('work_orders', sql)
    from collections import Counter
    print('Rows', len(rows), 'Unique WOs', len({r['WIP_ENTITY_ID'] for r in rows}))
    for col in ['WO_TYPE','WORK_ORDER_STATUS','FAILURE_CODE','SHUTDOWN_TYPE_DISP','ACTIVITY_CAUSE_DISP']:
        print(col, Counter(r[col] for r in rows).most_common(15))
    print('Failure dates populated', sum(bool(r['FAILURE_DATE']) for r in rows))
    meta = query('runtime_discovery', """SELECT OWNER,TABLE_NAME,COLUMN_NAME FROM ALL_TAB_COLUMNS
WHERE OWNER IN ('EAM','CSI') AND TABLE_NAME IN ('EAM_ASSET_METERS','CSI_COUNTER_ASSOCIATIONS','CSI_COUNTERS_B','CSI_COUNTER_READINGS')
ORDER BY OWNER,TABLE_NAME,COLUMN_ID;""")
    print('Runtime metadata', meta)
