from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any


def _title_from_stem(stem: str) -> str:
    return stem.removeprefix("run_").replace("_", " ").title()


def _literal(node: ast.AST | None, default: Any = None) -> Any:
    if node is None:
        return default
    try:
        return ast.literal_eval(node)
    except (ValueError, TypeError):
        return default


def _parse_custom_script(script_path: Path) -> dict[str, Any]:
    source = script_path.read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(source, filename=str(script_path))
    description = ast.get_docstring(tree) or f"Run {_title_from_stem(script_path.stem)}."
    arguments: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        if node.func.attr != "add_argument" or not node.args:
            continue
        flag = _literal(node.args[0])
        if not isinstance(flag, str) or not flag.startswith("--"):
            continue
        keywords = {item.arg: item.value for item in node.keywords if item.arg}
        action = _literal(keywords.get("action"))
        type_node = keywords.get("type")
        arg_type = type_node.id if isinstance(type_node, ast.Name) else "str"
        arguments.append({
            "flag": flag,
            "name": flag[2:].replace("-", "_"),
            "label": flag[2:].replace("-", " ").title(),
            "help": _literal(keywords.get("help"), ""),
            "required": bool(_literal(keywords.get("required"), False)),
            "default": _literal(keywords.get("default")),
            "type": "bool" if action in {"store_true", "store_false"} else arg_type,
            "action": action,
        })

    output_match = re.search(r'OUTPUT_BASE_DIR\s*/\s*["\']([^"\']+)["\']', source)
    report = {
        "id": script_path.stem.removeprefix("run_"),
        "name": _title_from_stem(script_path.stem),
        "description": description.splitlines()[0],
        "script": script_path.name,
        "category": output_match.group(1) if output_match else None,
        "arguments": arguments,
    }
    legacy_overrides = {
        "run_qa_daily_report.py": {
            "id": "qa_daily",
            "name": "QA Daily Results",
            "description": "QA results for the last 24 hours.",
            "category": "qa_daily_results",
        },
        "run_level10_dm_report.py": {
            "id": "level10_dm",
            "name": "Level 10 DM Open Work Orders",
            "description": "Open work orders for Level 10 DM.",
            "category": "level10_dm_open",
        },
        "run_pm_released_wo_report.py": {
            "id": "pm_released_wo",
            "name": "PM Released Work Orders",
            "description": "Released preventive maintenance work orders.",
            "category": "pm_released_work_orders",
        },
    }
    report.update(legacy_overrides.get(script_path.name, {}))
    return report


def get_report_catalog(project_root: Path) -> list[dict[str, Any]]:
    scripts_dir = project_root / "scripts"
    reports: dict[str, dict[str, Any]] = {}

    try:
        from scripts.query_runner import QUERY_DEFINITIONS

        for report_id, definition in QUERY_DEFINITIONS.items():
            reports[definition.script_name] = {
                "id": report_id,
                "name": _title_from_stem(Path(definition.script_name).stem),
                "description": definition.description,
                "script": definition.script_name,
                "category": definition.output_dir,
                "arguments": [
                    {
                        "flag": arg.flag,
                        "name": arg.flag[2:].replace("-", "_"),
                        "label": arg.flag[2:].replace("-", " ").title(),
                        "help": arg.help,
                        "required": arg.required,
                        "default": arg.default,
                        "type": "int" if arg.arg_type is int else "str",
                        "action": None,
                    }
                    for arg in definition.args
                ],
            }
    except ImportError:
        pass

    for script_path in sorted(scripts_dir.glob("run_*.py")):
        if script_path.name == "run_all_reports.py":
            continue
        if script_path.name not in reports:
            reports[script_path.name] = _parse_custom_script(script_path)

    return sorted(reports.values(), key=lambda item: item["name"].lower())


def get_report(project_root: Path, report_id: str) -> dict[str, Any] | None:
    return next(
        (report for report in get_report_catalog(project_root) if report["id"] == report_id),
        None,
    )


def build_script_arguments(report: dict[str, Any], values: dict[str, Any]) -> list[str]:
    allowed = {arg["name"]: arg for arg in report["arguments"]}
    unknown = sorted(set(values) - set(allowed))
    if unknown:
        raise ValueError(f"Unknown argument(s): {', '.join(unknown)}")

    command: list[str] = []
    for name, spec in allowed.items():
        value = values.get(name)
        if value in (None, ""):
            if spec["required"]:
                raise ValueError(f"{spec['label']} is required")
            continue
        if spec["type"] == "bool":
            if bool(value):
                command.append(spec["flag"])
            continue
        if spec["type"] == "int":
            try:
                value = int(value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{spec['label']} must be an integer") from exc
        command.extend([spec["flag"], str(value)])
    return command
