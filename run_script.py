from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


def available_scripts() -> list[str]:
    return sorted(
        path.name
        for path in SCRIPTS_DIR.glob("*.py")
        if path.name not in {"__init__.py", "query_runner.py"}
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="List or run any project script with the project import path configured."
    )
    parser.add_argument("script", nargs="?", help="Script filename, with or without .py.")
    parser.add_argument("script_args", nargs=argparse.REMAINDER, help="Arguments passed to the script.")
    parser.add_argument("--list", action="store_true", help="List available scripts.")
    args = parser.parse_args()

    scripts = available_scripts()
    if args.list or not args.script:
        print("\n".join(scripts))
        return 0

    script_name = args.script if args.script.endswith(".py") else f"{args.script}.py"
    if script_name not in scripts:
        parser.error(f"Unknown script: {script_name}")

    environment = os.environ.copy()
    existing_pythonpath = environment.get("PYTHONPATH")
    environment["PYTHONPATH"] = str(PROJECT_ROOT) + (
        os.pathsep + existing_pythonpath if existing_pythonpath else ""
    )
    result = subprocess.run(
        [sys.executable, str(SCRIPTS_DIR / script_name), *args.script_args],
        cwd=PROJECT_ROOT,
        env=environment,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
