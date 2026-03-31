from datetime import datetime
from pathlib import Path

from oracledb_connector import OracleDBConnector
from configuration.config import SQL_DIR, OUTPUT_BASE_DIR
from configuration.orcdb_logger import (
    set_request_id,
    info,
    error,
    timed_operation,
)
from configuration.utils.report_utility import ReportUtility


def main():
    set_request_id()
    info("Starting Level 10 DM Open Work Orders report")

    oracle = OracleDBConnector()

    # Output directory
    output_dir = OUTPUT_BASE_DIR / "level10_dm_open"
    output_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped output files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = output_dir / f"level10_dm_open_{timestamp}.csv"
    excel_file = output_dir / f"level10_dm_open_{timestamp}.xlsx"

    # SQL script
    sql_file = SQL_DIR / "level10_dm_open.sql"

    # Run SQLcl → CSV
    with timed_operation("level10_dm_sql_execution"):
        result = oracle.run_sql_script(
            str(sql_file),
            str(csv_file)
        )

        if result.returncode != 0:
            error("Level 10 DM report failed")
            error(result.stderr)
            raise RuntimeError("SQLcl execution failed")

    info(f"CSV report generated: {csv_file}")

    # Convert CSV → Excel
    with timed_operation("level10_dm_excel_generation"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name="Level 10 DM Open"
        )

    info(f"Excel report generated: {excel_file}")


if __name__ == "__main__":
    main()
