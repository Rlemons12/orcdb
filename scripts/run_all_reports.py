from pathlib import Path
import shutil
import time

from configuration.orcdb_logger import (
    set_request_id,
    info,
    error,
)

# Import the individual report runners
from run_qa_daily_report import main as run_qa_daily
from run_qa_report_12hr import main as run_qa_12hr
from run_level10_dm_report import main as run_level10_dm

from configuration.config import (
    QA_DAILY_RESULTS_DIR,
    QA_RESULTS_DIR,
    OUTPUT_BASE_DIR,
)

# ------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------

COMBINED_OUTPUT_DIR = OUTPUT_BASE_DIR / "combined_reports"


# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------

def get_latest_xlsx(directory: Path) -> Path:
    """
    Return the most recently modified XLSX file in a directory.
    """
    xlsx_files = list(directory.glob("*.xlsx"))
    if not xlsx_files:
        raise FileNotFoundError(f"No XLSX files found in {directory}")

    return max(xlsx_files, key=lambda p: p.stat().st_mtime)


def copy_to_combined(file_path: Path):
    """
    Copy an XLSX file into the combined reports folder.
    """
    COMBINED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = COMBINED_OUTPUT_DIR / file_path.name
    shutil.copy2(file_path, destination)
    info(f"Copied report to combined folder: {destination}")


# ------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------

def main():
    set_request_id()
    info("Starting full report batch run")

    try:
        # -------------------------------
        # QA Daily (24h)
        # -------------------------------
        info("Running QA Daily Results report")
        run_qa_daily()
        time.sleep(1)  # ensure filesystem timestamp difference
        latest = get_latest_xlsx(QA_DAILY_RESULTS_DIR)
        copy_to_combined(latest)

        # -------------------------------
        # QA Results (12h)
        # -------------------------------
        info("Running QA Results (12 hours) report")
        run_qa_12hr()
        time.sleep(1)
        latest = get_latest_xlsx(QA_RESULTS_DIR)
        copy_to_combined(latest)

        # -------------------------------
        # Level 10 DM Open WOs
        # -------------------------------
        level10_dir = OUTPUT_BASE_DIR / "level10_dm_open"
        info("Running Level 10 DM Open Work Orders report")
        run_level10_dm()
        time.sleep(1)
        latest = get_latest_xlsx(level10_dir)
        copy_to_combined(latest)

        info("All reports completed successfully")

    except Exception as exc:
        error(f"Report batch failed: {exc}")
        raise


if __name__ == "__main__":
    main()
