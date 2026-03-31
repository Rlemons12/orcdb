from __future__ import annotations

import argparse
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from configuration.config import OUTPUT_BASE_DIR, SQL_DIR, ensure_output_dirs
from configuration.orcdb_logger import error, info, set_request_id, timed_operation
from configuration.utils.report_utility import ReportUtility
from oracledb_connector import OracleDBConnector


@dataclass(frozen=True)
class ArgSpec:
    flag: str
    token: str
    help: str
    arg_type: type = str
    default: object | None = None
    required: bool = False
    upper: bool = False
    sql_kind: str = "string"


@dataclass(frozen=True)
class QueryDefinition:
    script_name: str
    description: str
    sql_file: str
    output_dir: str
    file_prefix: str
    sheet_name: str
    args: tuple[ArgSpec, ...] = ()


def _sql_literal(value: object, kind: str, upper: bool = False) -> str:
    if kind == "int":
        return str(int(value))

    text = str(value).strip()
    if upper:
        text = text.upper()
    text = text.replace("'", "''")
    return f"'{text}'"


def _clean_csv(csv_path: Path) -> int:
    lines = csv_path.read_text(encoding="utf-8", errors="replace").splitlines()

    start = 0
    for index, line in enumerate(lines):
        if line.strip() and "," in line:
            start = index
            break

    csv_path.write_text("\n".join(lines[start:]) + "\n", encoding="utf-8")
    return start


QUERY_DEFINITIONS: dict[str, QueryDefinition] = {
    "verify_org_mapping": QueryDefinition(
        script_name="run_verify_org_mapping.py",
        description="Verify org code and org ID mapping.",
        sql_file="verify_org_mapping.sql",
        output_dir="verify_org_mapping",
        file_prefix="verify_org_mapping",
        sheet_name="Org Mapping",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code to look up.", default="XAU", upper=True),
        ),
    ),
    "lookup_user": QueryDefinition(
        script_name="run_lookup_user.py",
        description="Look up a user by user name, user ID, or employee ID.",
        sql_file="lookup_user.sql",
        output_dir="lookup_user",
        file_prefix="lookup_user",
        sheet_name="User Lookup",
        args=(
            ArgSpec("--identifier", "IDENTIFIER", "User name, user ID, or employee ID.", required=True),
        ),
    ),
    "users_by_responsibility": QueryDefinition(
        script_name="run_users_by_eam_responsibility.py",
        description="Find active users with a responsibility.",
        sql_file="users_by_responsibility.sql",
        output_dir="users_by_responsibility",
        file_prefix="users_by_responsibility",
        sheet_name="Users By Resp",
        args=(
            ArgSpec("--responsibility-name", "RESPONSIBILITY_NAME", "Responsibility name.", default="ICU EAM Manager - XAU"),
            ArgSpec("--app-short-name", "APP_SHORT_NAME", "Application short name.", default="EAM", upper=True),
        ),
    ),
    "user_responsibilities": QueryDefinition(
        script_name="run_user_responsibilities.py",
        description="Find all responsibilities assigned to a user.",
        sql_file="user_responsibilities.sql",
        output_dir="user_responsibilities",
        file_prefix="user_responsibilities",
        sheet_name="User Resp",
        args=(
            ArgSpec("--identifier", "IDENTIFIER", "User name, user ID, or employee ID.", required=True),
        ),
    ),
    "qa_groups_for_user": QueryDefinition(
        script_name="run_qa_groups_for_user.py",
        description="Find QA groups for a user.",
        sql_file="qa_groups_for_user.sql",
        output_dir="qa_groups_for_user",
        file_prefix="qa_groups_for_user",
        sheet_name="QA Groups",
        args=(
            ArgSpec("--identifier", "IDENTIFIER", "User name, user ID, or employee ID.", required=True),
        ),
    ),
    "qa_group_members": QueryDefinition(
        script_name="run_qa_group_members.py",
        description="Find all active members of a QA group.",
        sql_file="qa_group_members.sql",
        output_dir="qa_group_members",
        file_prefix="qa_group_members",
        sheet_name="QA Group Members",
        args=(
            ArgSpec("--group-name", "GROUP_NAME", "Exact QA group name.", required=True),
        ),
    ),
    "released_work_orders_for_asset": QueryDefinition(
        script_name="run_released_work_orders_for_asset.py",
        description="List released work orders for an asset.",
        sql_file="released_work_orders_for_asset.sql",
        output_dir="released_work_orders_for_asset",
        file_prefix="released_work_orders_for_asset",
        sheet_name="Released WOs",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--asset-number", "ASSET_NUMBER", "Asset number.", required=True),
        ),
    ),
    "qa_results_for_work_order": QueryDefinition(
        script_name="run_qa_results_for_work_order.py",
        description="QA results for a work order with technician name.",
        sql_file="qa_results_for_work_order.sql",
        output_dir="qa_results_for_work_order",
        file_prefix="qa_results_for_work_order",
        sheet_name="QA Results",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--work-order", "WORK_ORDER", "Work order number.", required=True),
        ),
    ),
    "parts_charged_to_work_order": QueryDefinition(
        script_name="run_parts_charged_to_work_order.py",
        description="Parts charged to a work order.",
        sql_file="parts_charged_to_work_order.sql",
        output_dir="parts_charged_to_work_order",
        file_prefix="parts_charged_to_work_order",
        sheet_name="Parts Charged",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--work-order", "WORK_ORDER", "Work order number.", required=True),
        ),
    ),
    "resources_for_employee": QueryDefinition(
        script_name="run_resources_for_employee.py",
        description="Find resources assigned to an employee.",
        sql_file="resources_for_employee.sql",
        output_dir="resources_for_employee",
        file_prefix="resources_for_employee",
        sheet_name="Employee Resources",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--name", "NAME", "Full or partial employee name.", required=True),
        ),
    ),
    "work_order_operations": QueryDefinition(
        script_name="run_work_order_operations.py",
        description="Work order operations with department details.",
        sql_file="work_order_operations.sql",
        output_dir="work_order_operations",
        file_prefix="work_order_operations",
        sheet_name="WO Operations",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--work-order", "WORK_ORDER", "Work order number.", required=True),
        ),
    ),
    "qa_results_with_group": QueryDefinition(
        script_name="run_qa_results_with_group.py",
        description="QA results enriched with QA group membership.",
        sql_file="qa_results_with_group.sql",
        output_dir="qa_results_with_group",
        file_prefix="qa_results_with_group",
        sheet_name="QA With Group",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--days", "DAYS", "Rolling number of days.", arg_type=int, default=1, sql_kind="int"),
        ),
    ),
    "person_work_order_history": QueryDefinition(
        script_name="run_person_wo_history.py",
        description="All work orders completed by a named employee.",
        sql_file="person_work_order_history.sql",
        output_dir="person_work_order_history",
        file_prefix="person_work_order_history",
        sheet_name="Person History",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--name", "NAME", "Full or partial employee name.", required=True),
            ArgSpec("--days", "DAYS", "Rolling number of days.", arg_type=int, default=90, sql_kind="int"),
        ),
    ),
    "top_part_transactions": QueryDefinition(
        script_name="run_top_part_transactions.py",
        description="Work orders with the most part transactions.",
        sql_file="top_part_transactions.sql",
        output_dir="top_part_transactions",
        file_prefix="top_part_transactions",
        sheet_name="Top Part Trans",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--days", "DAYS", "Rolling number of days.", arg_type=int, default=30, sql_kind="int"),
            ArgSpec("--limit", "LIMIT", "Maximum number of rows.", arg_type=int, default=10, sql_kind="int"),
        ),
    ),
    "audit_trail_quick": QueryDefinition(
        script_name="run_audit_trail_quick.py",
        description="Quick audit trail for one user ID.",
        sql_file="audit_trail_quick.sql",
        output_dir="audit_trail_quick",
        file_prefix="audit_trail_quick",
        sheet_name="Audit Quick",
        args=(
            ArgSpec("--user-id", "USER_ID", "Oracle USER_ID to inspect.", arg_type=int, required=True, sql_kind="int"),
        ),
    ),
    "audit_trail_full": QueryDefinition(
        script_name="run_audit_trail_full.py",
        description="Full audit trail for one user ID with a start date filter.",
        sql_file="audit_trail_full.sql",
        output_dir="audit_trail_full",
        file_prefix="audit_trail_full",
        sheet_name="Audit Full",
        args=(
            ArgSpec("--user-id", "USER_ID", "Oracle USER_ID to inspect.", arg_type=int, required=True, sql_kind="int"),
            ArgSpec("--date-from", "DATE_FROM", "Start date in YYYY-MM-DD format.", required=True),
        ),
    ),
    "work_order_full_picture": QueryDefinition(
        script_name="run_work_order_full_picture.py",
        description="Full work order picture with operations, QA, and parts.",
        sql_file="work_order_full_picture.sql",
        output_dir="work_order_full_picture",
        file_prefix="work_order_full_picture",
        sheet_name="WO Full Picture",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--work-order", "WORK_ORDER", "Work order number.", required=True),
        ),
    ),
    "asset_reliability_summary": QueryDefinition(
        script_name="run_asset_reliability_summary.py",
        description="Asset reliability summary.",
        sql_file="asset_reliability_summary.sql",
        output_dir="asset_reliability_summary",
        file_prefix="asset_reliability_summary",
        sheet_name="Asset Reliability",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--months", "MONTHS", "Rolling number of months.", arg_type=int, default=12, sql_kind="int"),
            ArgSpec("--limit", "LIMIT", "Maximum number of rows.", arg_type=int, default=20, sql_kind="int"),
        ),
    ),
    "technician_productivity_summary": QueryDefinition(
        script_name="run_technician_productivity_summary.py",
        description="Technician productivity summary.",
        sql_file="technician_productivity_summary.sql",
        output_dir="technician_productivity_summary",
        file_prefix="technician_productivity_summary",
        sheet_name="Tech Productivity",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--months", "MONTHS", "Rolling number of months.", arg_type=int, default=3, sql_kind="int"),
            ArgSpec("--limit", "LIMIT", "Maximum number of rows.", arg_type=int, default=20, sql_kind="int"),
        ),
    ),
    "parts_consumption_by_asset": QueryDefinition(
        script_name="run_parts_consumption_by_asset.py",
        description="Parts consumption by asset.",
        sql_file="parts_consumption_by_asset.sql",
        output_dir="parts_consumption_by_asset",
        file_prefix="parts_consumption_by_asset",
        sheet_name="Parts By Asset",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--asset-number", "ASSET_NUMBER", "Asset number.", required=True),
            ArgSpec("--months", "MONTHS", "Rolling number of months.", arg_type=int, default=12, sql_kind="int"),
        ),
    ),
    "employees_for_resource": QueryDefinition(
        script_name="run_employees_for_resource.py",
        description="Employees assigned to a resource.",
        sql_file="employees_for_resource.sql",
        output_dir="employees_for_resource",
        file_prefix="employees_for_resource",
        sheet_name="Resource Employees",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--resource-code", "RESOURCE_CODE", "Resource code.", required=True),
        ),
    ),
    "work_orders_for_department": QueryDefinition(
        script_name="run_work_orders_for_department.py",
        description="Work orders for a department.",
        sql_file="work_orders_for_department.sql",
        output_dir="work_orders_for_department",
        file_prefix="work_orders_for_department",
        sheet_name="Dept Work Orders",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
            ArgSpec("--department-code", "DEPARTMENT_CODE", "Department code.", required=True),
            ArgSpec("--days", "DAYS", "Rolling number of days.", arg_type=int, default=90, sql_kind="int"),
        ),
    ),
    "resource_roster": QueryDefinition(
        script_name="run_resource_roster.py",
        description="Full active person-resource roster.",
        sql_file="resource_roster.sql",
        output_dir="resource_roster",
        file_prefix="resource_roster",
        sheet_name="Resource Roster",
        args=(
            ArgSpec("--org-code", "ORG_CODE", "Organization code.", default="XAU", upper=True),
        ),
    ),
}


def run_named_query(query_name: str) -> None:
    definition = QUERY_DEFINITIONS[query_name]

    parser = argparse.ArgumentParser(description=definition.description)
    for arg in definition.args:
        kwargs: dict[str, object] = {"help": arg.help, "type": arg.arg_type}
        if arg.required:
            kwargs["required"] = True
        else:
            kwargs["default"] = arg.default
        parser.add_argument(arg.flag, **kwargs)

    args = parser.parse_args()

    set_request_id()
    ensure_output_dirs()

    sql_template = SQL_DIR / definition.sql_file
    if not sql_template.exists():
        raise FileNotFoundError(f"Missing SQL template: {sql_template}")

    output_dir = OUTPUT_BASE_DIR / definition.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_file = output_dir / f"{definition.file_prefix}_{timestamp}.csv"
    excel_file = output_dir / f"{definition.file_prefix}_{timestamp}.xlsx"

    info(f"Starting {definition.description}")
    info(f"SQL template: {sql_template}")
    info(f"CSV output: {csv_file}")
    info(f"Excel output: {excel_file}")

    sql_text = sql_template.read_text(encoding="utf-8")
    for arg in definition.args:
        value = getattr(args, arg.flag.lstrip("-").replace("-", "_"))
        sql_text = sql_text.replace(
            f"__{arg.token}__",
            _sql_literal(value, arg.sql_kind, upper=arg.upper),
        )

    tmp_sql = tempfile.NamedTemporaryFile(mode="w", suffix=".sql", delete=False, encoding="utf-8")
    tmp_sql.write(sql_text)
    tmp_sql.close()

    oracle = OracleDBConnector()

    with timed_operation(f"query_execution:{definition.file_prefix}"):
        result = oracle.run_sql_script(tmp_sql.name, str(csv_file))

    Path(tmp_sql.name).unlink(missing_ok=True)

    if result.returncode != 0:
        error(result.stderr.strip())
        raise RuntimeError(f"SQLcl execution failed for {definition.file_prefix}")

    if not csv_file.exists() or csv_file.stat().st_size == 0:
        raise RuntimeError(f"No output created for {definition.file_prefix}")

    stripped = _clean_csv(csv_file)
    info(f"Stripped {stripped} SQLcl banner line(s)")

    with timed_operation(f"excel_generation:{definition.file_prefix}"):
        ReportUtility.csv_to_excel(
            csv_path=csv_file,
            excel_path=excel_file,
            sheet_name=definition.sheet_name[:31],
        )

    info(f"Report complete: {excel_file}")
