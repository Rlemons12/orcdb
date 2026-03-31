from datetime import datetime
from pathlib import Path

from oracledb_connector import OracleDBConnector
from configuration.orcdb_logger import (
    set_request_id,
    info,
    error,
    timed_operation,
)
from configuration.config import (
    SQL_DIR,
    PM_RELEASED_WO_DIR,
    ensure_output_dirs,
)
from configuration.utils.report_utility import ReportUtility


def main():
    # One request ID per run
    set_request_id()
    ensure_output_dirs()

    info("Starting PM Released Work Orders report")

    oracle = OracleDBConnector()

    # Timestamped output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = PM_RELEASED_WO_DIR / f"pm_released_work_orders_{timestamp}.csv"
    excel_file = PM_RELEASED_WO_DIR / f"pm_released_work_orders_{timestamp}.xlsx"

    # SQL script
    sql_file = SQL_DIR / "pm_released_work_orders.sql"

    # Run SQLcl → CSV
    with timed_operation("pm_released_wo_sql_execution"):
        result = oracle.run_sql_script(
            str(sql_file),
            str(csv_file)
        )

        if result.returncode != 0:
            error("PM Released WO report failed")
            error(result.stderr.strip())
            raise RuntimeError("SQLcl execution failed")

    info(f"CSV report generated: {csv_file}")

    # Convert CSV → Excel
    with timed_operation("pm_released_wo_excel_generation"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name="PM Released Work Orders"
        )

    info(f"Excel report generated: {excel_file}")


if __name__ == "__main__":
    main()
