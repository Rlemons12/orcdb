import logging
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent
LOG_FILE = LOG_DIR / "email_service.log"

logger = logging.getLogger("email_service")
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s",
    "%Y-%m-%d %H:%M:%S"
))

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
))

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
