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
    QA_RESULTS_DIR,
    ensure_output_dirs,
)
from configuration.utils.report_utility import ReportUtility


def main():
    set_request_id()
    ensure_output_dirs()

    info("Starting QA Results Report (Last 12 Hours)")

    oracle = OracleDBConnector()

    # Timestamped output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = QA_RESULTS_DIR / f"qa_results_12{timestamp}.csv"
    excel_file = QA_RESULTS_DIR / f"qa_results_12{timestamp}.xlsx"

    # SQL script
    sql_file = SQL_DIR / "qa_results_last_12_hours.sql"

    # Run SQLcl → CSV
    with timed_operation("qa_results_sql_execution"):
        result = oracle.run_sql_script(
            str(sql_file),
            str(csv_file)
        )

        if result.returncode != 0:
            error("QA report failed")
            error(result.stderr.strip())
            raise RuntimeError("SQLcl execution failed")

    info(f"CSV report generated: {csv_file}")

    # CSV → Excel using ReportUtility
    with timed_operation("qa_results_excel_generation"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name="QA Results (12 Hours)"
        )

    info(f"Excel report generated: {excel_file}")


if __name__ == "__main__":
    main()
