import logging
import os
import sys
import uuid
import time
import threading
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

# ------------------------------------------------------------------
# BASE DIRECTORY
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ------------------------------------------------------------------
# LOGGER SETUP
# ------------------------------------------------------------------

LOGGER_NAME = "orcdb_logger"
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)
logger.propagate = False

LOG_FILE = LOG_DIR / "orcdb.log"

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=5,
    encoding="utf-8"
)

console_handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - "
    "%(filename)s:%(lineno)d - %(funcName)s() - "
    "[REQ-%(request_id)s] %(message)s"
)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# ------------------------------------------------------------------
# REQUEST / RUN ID SUPPORT
# ------------------------------------------------------------------

_thread_local = threading.local()


def _generate_request_id():
    return str(uuid.uuid4())[:8]


def get_request_id():
    return getattr(_thread_local, "request_id", None)


def set_request_id(request_id: str | None = None):
    _thread_local.request_id = request_id or _generate_request_id()
    return _thread_local.request_id


def clear_request_id():
    if hasattr(_thread_local, "request_id"):
        delattr(_thread_local, "request_id")


class RequestIdAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        kwargs["extra"] = kwargs.get("extra", {})
        kwargs["extra"]["request_id"] = get_request_id() or "--------"
        return msg, kwargs


log = RequestIdAdapter(logger, {})

# ------------------------------------------------------------------
# CONVENIENCE LOG FUNCTIONS
# ------------------------------------------------------------------

def debug(msg: str):
    log.debug(msg)


def info(msg: str):
    log.info(msg)


def warning(msg: str):
    log.warning(msg)


def error(msg: str):
    log.error(msg)


def critical(msg: str):
    log.critical(msg)

# ------------------------------------------------------------------
# TIMED OPERATION CONTEXT
# ------------------------------------------------------------------

class timed_operation:
    def __init__(self, name: str):
        self.name = name
        self.request_id = get_request_id() or set_request_id()

    def __enter__(self):
        self.start = time.time()
        debug(f"Starting operation: {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start
        if exc_type:
            error(f"Operation failed: {self.name} ({duration:.3f}s) | {exc_val}")
        else:
            debug(f"Completed operation: {self.name} ({duration:.3f}s)")

# ------------------------------------------------------------------
# ORACLE-SPECIFIC HELPERS
# ------------------------------------------------------------------

def log_db_connect_start(user, host, service):
    info(f"Oracle connect start | user={user} host={host} service={service}")


def log_db_connect_success():
    info("Oracle connection established")


def log_db_connect_failure(err):
    error(f"Oracle connection failed | {err}")


def log_sql_start(sql_file):
    info(f"Executing SQL script: {sql_file}")


def log_sql_success(duration):
    info(f"SQL execution completed in {duration:.3f}s")


def log_sql_failure(err):
    error(f"SQL execution failed | {err}")
