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
    QA_MONTHLY_RESULTS_DIR,
    ensure_output_dirs,
)
from configuration.utils.report_utility import ReportUtility


def main():
    set_request_id()
    ensure_output_dirs()

    info("Starting QA Monthly Results (31 days) report")

    oracle = OracleDBConnector()

    # Timestamped output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = QA_MONTHLY_RESULTS_DIR / f"qa_monthly_results_{timestamp}.csv"
    excel_file = QA_MONTHLY_RESULTS_DIR / f"qa_monthly_results_{timestamp}.xlsx"

    # SQL script
    sql_file = SQL_DIR / "qa_results_last_31_days.sql"

    # Run SQLcl → CSV
    with timed_operation("qa_monthly_results_sql_execution"):
        result = oracle.run_sql_script(
            str(sql_file),
            str(csv_file)
        )

        if result.returncode != 0:
            error("QA Monthly Results report failed")
            error(result.stderr.strip())
            raise RuntimeError("SQLcl execution failed")

    info(f"CSV report generated: {csv_file}")

    # Convert CSV → Excel
    with timed_operation("qa_monthly_results_excel_generation"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name="QA Monthly Results"
        )

    info(f"Excel report generated: {excel_file}")


if __name__ == "__main__":
    main()
