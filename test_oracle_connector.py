from pathlib import Path

from oracledb_connector import OracleDBConnector
from configuration.orcdb_logger import (
    set_request_id,
    info,
    error,
    critical,
    timed_operation,
)


def main():
    script_name = "test_oracle_connector.py"

    # Create a request/run ID for this script execution
    set_request_id()

    info(f"▶ START script: {script_name}")

    oracle = OracleDBConnector()
    test_sql_file = None

    try:
        with timed_operation("test_database_connection"):
            info("Testing database connection")
            oracle.test_connection()

        with timed_operation("inline_sql_test"):
            info("Running inline SQL test via SQLcl")

            # Inline SQL test (read-only, safe)
            test_sql = """
            SET HEADING OFF
            SET FEEDBACK OFF
            SELECT 'TEST_OK' FROM dual;
            EXIT
            """

            test_sql_file = Path("test_connection.sql")
            test_sql_file.write_text(test_sql.strip(), encoding="utf-8")

            result = oracle.run_sql_script(str(test_sql_file))

            if result.returncode != 0:
                error("SQL execution failed")
                error(result.stderr.strip())
                raise RuntimeError("SQLcl execution failed")

            info("SQL execution succeeded")
            info("SQLcl output:")
            info(result.stdout.strip())

    except Exception as exc:
        critical(f"Test failed: {exc}")
        raise

    finally:
        # Cleanup temp SQL file
        if test_sql_file and test_sql_file.exists():
            test_sql_file.unlink()
            info("Temporary SQL file cleaned up")

        info(f"■ END script: {script_name}")


if __name__ == "__main__":
    main()
