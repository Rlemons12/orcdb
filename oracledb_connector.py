import os
import re
import subprocess
import time
from pathlib import Path
from dotenv import load_dotenv

# Standalone project logger
from configuration.orcdb_logger import (
    set_request_id,
    timed_operation,
    log_db_connect_start,
    log_db_connect_success,
    log_db_connect_failure,
    log_sql_start,
    log_sql_success,
    log_sql_failure,
    info,
    warning,
)


class OracleDBConnector:
    """
    Oracle SQLcl connector using read-only credentials.

    Builds:
        sql.exe username/password@host:port/service_name

    Executes SQL scripts via SQLcl (SPOOL supported).
    """

    def __init__(self, env_file: str | None = None):
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            load_dotenv()

        # Create a request/run ID for this connector instance
        set_request_id()

        info("Initializing OracleDBConnector")

        # Load required env vars
        self.sqlcl_path = self._get_env("SQLCL_PATH")
        self.username   = self._get_env("ORACLE_USERNAME")
        self.password   = self._get_env("ORACLE_PASSWORD")
        self.hostname   = self._get_env("ORACLE_HOSTNAME")
        self.port       = self._get_env("ORACLE_PORT")
        self.service_name = self._get_env("ORACLE_SERVICE_NAME")

    # -------------------------------------------------
    # Helpers
    # -------------------------------------------------

    def _get_env(self, key: str) -> str:
        value = os.getenv(key)
        if not value:
            raise RuntimeError(f"Missing required environment variable: {key}")
        return value

    @property
    def dsn(self) -> str:
        """host:port/service_name"""
        return f"{self.hostname}:{self.port}/{self.service_name}"

    @property
    def connect_string(self) -> str:
        """username/password@host:port/service_name"""
        return f"{self.username}/{self.password}@{self.dsn}"

    def _build_sqlcl_stdin(self, sql_text: str) -> str:
        cleaned = sql_text.lstrip("\ufeff")
        cleaned = re.sub(r"(?im)^\s*SPOOL\b.*$", "", cleaned)
        cleaned = re.sub(r"(?im)^\s*EXIT\s*;?\s*$", "", cleaned)
        return cleaned.rstrip() + "\nEXIT\n"

    def _run_sql_via_stdin(self, sql_text: str) -> subprocess.CompletedProcess[str]:
        cmd = [
            self.sqlcl_path,
            "-S",
            self.connect_string,
        ]
        return subprocess.run(
            cmd,
            input=self._build_sqlcl_stdin(sql_text),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )

    # -------------------------------------------------
    # Public API
    # -------------------------------------------------

    def test_connection(self) -> None:
        """Simple SELECT test to verify connectivity."""

        with timed_operation("oracle_test_connection"):
            log_db_connect_start(
                user=self.username,
                host=self.hostname,
                service=self.service_name
            )

            cmd = [
                self.sqlcl_path,
                self.connect_string
            ]

            result = subprocess.run(
                cmd,
                input="SELECT SYSDATE FROM dual;\nexit\n",
                text=True,
                capture_output=True
            )

            if result.returncode != 0:
                log_db_connect_failure(result.stderr.strip())
                raise RuntimeError(f"Connection failed:\n{result.stderr}")

            log_db_connect_success()

    def run_sql_script(self, sql_file: str, output_file: str):
        """
        Execute a SQL file using SQLcl with a single substitution argument (&1).
        """
        sql_path = Path(sql_file)
        if not sql_path.exists():
            raise FileNotFoundError(f"SQL file not found: {sql_file}")

        output_path = Path(output_file)

        with timed_operation(f"sql_execution:{sql_path.name}"):
            log_sql_start(str(sql_path))

            start_time = time.time()

            cmd = [
                self.sqlcl_path,
                "-S",  # silent / non-interactive (CRITICAL)
                self.connect_string,
                f"@{sql_path}",
                str(output_file),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )

            if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
                duration = time.time() - start_time
                log_sql_success(duration)
                return result

            warning(
                "SQLcl file execution did not create output; falling back to stdin capture"
            )

            sql_text = sql_path.read_text(encoding="utf-8-sig")
            fallback_result = self._run_sql_via_stdin(sql_text)

            if fallback_result.returncode == 0:
                csv_output = fallback_result.stdout.strip()
                if csv_output:
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    output_path.write_text(csv_output + "\n", encoding="utf-8")

            duration = time.time() - start_time

            effective_result = fallback_result if fallback_result.returncode == 0 else result

            if effective_result.returncode != 0:
                log_sql_failure(
                    (effective_result.stderr or effective_result.stdout).strip()
                )
            else:
                log_sql_success(duration)

            return effective_result

    def run_query(self, sql: str) -> tuple[bool, str]:
        """
        Execute a single SQL statement via SQLcl stdin and return the raw output.

        Wraps the statement in minimal SQLcl formatting so the output is clean:
            SET PAGESIZE 0
            SET FEEDBACK OFF
            SET HEADING OFF
            SET ECHO OFF
            <your sql>;
            EXIT

        Returns:
            (success: bool, output: str)
            - success is True if returncode == 0
            - output is the stripped stdout content (the query result)

        Example:
            ok, out = oracle.run_query("SELECT COUNT(*) FROM APPS.QA_RESULTS")
            count = int(out.strip())
        """
        stdin_block = (
            "SET PAGESIZE 0\n"
            "SET FEEDBACK OFF\n"
            "SET HEADING OFF\n"
            "SET ECHO OFF\n"
            "SET LINESIZE 32767\n"
            "SET TRIMOUT ON\n"
            "SET TRIMSPOOL ON\n"
            f"{sql.rstrip(';')};\n"
            "EXIT\n"
        )

        cmd = [
            self.sqlcl_path,
            "-S",
            self.connect_string,
        ]

        result = self._run_sql_via_stdin(stdin_block)

        output = result.stdout.strip()
        success = result.returncode == 0

        return success, output
