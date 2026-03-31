from datetime import datetime

from oracledb_connector import OracleDBConnector
from configuration.orcdb_logger import (
    set_request_id,
    info,
    error,
    timed_operation,
)
from configuration.config import (
    SQL_DIR,
    CANCELLED_WO_DIR,
    ensure_output_dirs,
)
from configuration.utils.report_utility import ReportUtility


def main():
    set_request_id()
    ensure_output_dirs()

    info("Starting Cancelled Work Orders (15 days) report")

    oracle = OracleDBConnector()

    # Timestamped output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = CANCELLED_WO_DIR / f"cancelled_work_orders_{timestamp}.csv"
    excel_file = CANCELLED_WO_DIR / f"cancelled_work_orders_{timestamp}.xlsx"

    # SQL script
    sql_file = SQL_DIR / "cancelled_work_orders_15_days.sql"

    # Run SQLcl → CSV
    with timed_operation("cancelled_wo_sql_execution"):
        result = oracle.run_sql_script(
            str(sql_file),
            str(csv_file)
        )

        if result.returncode != 0:
            error("Cancelled WO report failed")
            error(result.stderr.strip())
            raise RuntimeError("SQLcl execution failed")

    info(f"CSV report generated: {csv_file}")

    # CSV → Excel using ReportUtility
    with timed_operation("cancelled_wo_excel_generation"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name="Cancelled Work Orders"
        )

    info(f"Excel report generated: {excel_file}")


if __name__ == "__main__":
    main()
