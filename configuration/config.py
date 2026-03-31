# configuration/config.py
from pathlib import Path

# ==================================================
# PROJECT ROOT
# ==================================================
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# ==================================================
# DIRECTORIES
# ==================================================

# SQL scripts
SQL_DIR = PROJECT_ROOT / "sql"

# Outputs
OUTPUT_BASE_DIR = PROJECT_ROOT / "outputs"

QA_RESULTS_DIR = OUTPUT_BASE_DIR / "qa_results_12"
CANCELLED_WO_DIR = OUTPUT_BASE_DIR / "cancelled_work_orders"
QA_DAILY_RESULTS_DIR = OUTPUT_BASE_DIR / "qa_daily_results"
QA_MONTHLY_RESULTS_DIR = OUTPUT_BASE_DIR / "qa_monthly_results"
PM_RELEASED_WO_DIR = OUTPUT_BASE_DIR / "pm_released_work_orders"

# ✅ NEW: Level 10 DM report
LEVEL10_DM_DIR = OUTPUT_BASE_DIR / "level10_dm"

# ==================================================
# HELPERS
# ==================================================
def ensure_output_dirs() -> None:
    """
    Create all required output directories.
    Safe to call on every run.
    """
    for path in (
        OUTPUT_BASE_DIR,
        QA_RESULTS_DIR,
        CANCELLED_WO_DIR,
        QA_DAILY_RESULTS_DIR,
        QA_MONTHLY_RESULTS_DIR,
        PM_RELEASED_WO_DIR,
        LEVEL10_DM_DIR,   # ✅ NEW
    ):
        path.mkdir(parents=True, exist_ok=True)
