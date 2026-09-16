# Scripts Reference

**Directory:** `scripts/`
**Last reviewed:** 2026-05-18
**Python scripts reviewed:** 66

This document summarizes what each script in `scripts/` does, the main command-line inputs, and the files or folders it writes. It is based on the current script sources, including docstrings, argument parsers, `query_runner` definitions, SQL template references, and SQLite/Oracle output paths.

## Main Groups

- **Oracle custom report runner:** 1 script(s)
- **Oracle discovery:** 2 script(s)
- **Oracle legacy report runner:** 6 script(s)
- **Oracle query_runner wrapper:** 32 script(s)
- **Oracle report orchestration:** 1 script(s)
- **Oracle verification:** 1 script(s)
- **Oracle workbook report:** 3 script(s)
- **SQLite BOM normalization:** 8 script(s)
- **SQLite BOM/drawing maintenance:** 2 script(s)
- **SQLite data cleanup:** 2 script(s)
- **SQLite export:** 1 script(s)
- **SQLite load:** 2 script(s)
- **SQLite schema cleanup:** 1 script(s)
- **SQLite schema rename:** 2 script(s)
- **SQLite schema repair:** 1 script(s)
- **Shared Oracle report infrastructure:** 1 script(s)

## Common Patterns

- Oracle report scripts use `OracleDBConnector`, SQLcl, and `configuration.config.OUTPUT_BASE_DIR` to write timestamped CSV and Excel files under `outputs/`.
- Thin `run_*` wrappers call `query_runner.run_named_query(...)`; the real SQL template, output folder, sheet name, and arguments are defined in `scripts/query_runner.py`.
- Asset PO lookups are currently an ad hoc Oracle workflow, not a checked-in `run_*` wrapper. Check direct WIP/requisition PO links first, then fall back to PO history for parts consumed on the asset if direct links return no rows.
- QA location-to-asset lookups are currently an ad hoc Oracle workflow, not a checked-in `run_*` wrapper. They combine Oracle Quality plan setup, plan Location lookup values, collection triggers, and EAM work-order asset history.
- Department asset-group exports are currently an ad hoc Oracle workflow, not a checked-in `run_*` wrapper. They read the EAM asset master view `APPS.MTL_EAM_ASSET_NUMBERS_ALL_V`, so they return actual assets in each asset group instead of only assets that have work-order history.
- SQLite BOM/drawing maintenance scripts operate on `data/BOM.db` by default. Most of the mutating scripts create a timestamped database backup unless `--no-backup` is supplied.
- The newer BOM pipeline is local SQLite-oriented: Oracle configured BOM exports are loaded from CSV into `BOM.db`, normalized into hierarchy tables, linked to drawings, and exported to an Excel workbook.

## Ad Hoc Asset PO Lookup Workflow

No script in `scripts/` currently owns this report. The April 2026 lookup used short Python snippets with `OracleDBConnector.run_sql_script(...)` and wrote results under `outputs/asset_pos/`.

Recommended order:

1. Query direct PO distributions for the asset work orders through `PO.PO_DISTRIBUTIONS_ALL.WIP_ENTITY_ID`.
2. If that returns no rows, query requisition lines through `PO.PO_REQUISITION_LINES_ALL.WIP_ENTITY_ID` and `PO.PO_REQ_DISTRIBUTIONS_ALL`.
3. If both direct paths are empty, use the consumed-parts fallback: find inventory items issued to the asset through `INV.MTL_MATERIAL_TRANSACTIONS`, then return PO lines for those item IDs in the same org and rolling date window.

Observed behavior:

- `AU-AFL31600-00` returned no rows when filtered by direct PO header creation date for the last 12 months.
- `AU-ACS7100-00` had 1,932 work orders in `XAU`, but no all-time direct WIP or requisition PO links.
- For `AU-ACS7100-00`, the consumed-parts fallback found 43 distinct parts used on the asset, 86 material issue transactions, 102 PO distribution lines, and 69 unique PO numbers in the last 12 months.

Typical output files:

- `outputs/asset_pos/asset_pos_<asset>_last12mo_<timestamp>.csv`
- `outputs/asset_pos/asset_pos_<asset>_last12mo_<timestamp>.xlsx`
- `outputs/asset_pos/asset_part_pos_<asset>_last12mo_<timestamp>.csv`
- `outputs/asset_pos/asset_part_pos_<asset>_last12mo_<timestamp>.xlsx`

The reusable SQL patterns are documented in `sql/orcdb_sql_queries.md` under "Purchasing / PO Lookup Notes".

## Ad Hoc QA Location To Asset Workflow

No script in `scripts/` currently owns this report. The April 2026 lookup used short Python snippets with `OracleDBConnector.run_sql_script(...)`, then joined intermediate CSV exports locally to avoid a very large Oracle join timing out.

Source tables/views:

- `QA.QA_PLANS` for collection plans such as `XAU MECH_FILLING PF`
- `QA.QA_PLAN_CHARS` and `QA.QA_CHARS` for prompts and result columns, such as `Location -> CHARACTER2`
- `QA.QA_PLAN_CHAR_VALUE_LOOKUPS` for the selectable Location list
- `APPS.QA_PLAN_COLLECTION_TRIGGERS_V` for plan triggers, especially `Asset Activity`
- `APPS.EAM_WORK_ORDERS_V` for assets tied to those asset activities
- `APPS.QA_RESULTS` for submitted result history

Recommended order:

1. Export XAU mechanical Location values by plan from `QA_PLAN_CHAR_VALUE_LOOKUPS`.
2. Export setup-based plan-to-asset mappings from `QA_PLAN_COLLECTION_TRIGGERS_V` joined to `EAM_WORK_ORDERS_V`.
3. Optionally export actual submitted-results mappings from `QA_RESULTS` joined to `EAM_WORK_ORDERS_V`.
4. Join the Location export to the asset mapping by `PLAN_ID` to produce `Location -> Plan -> Asset` rows.

Observed behavior:

- For work order `AU14947817`, plan `XAU MECH_FILLING PF` maps the `Location` field to `APPS.QA_RESULTS.CHARACTER2`.
- `XAU MECH_FILLING PF` is triggered by asset activity `AAA MECH_FILLING PF`, not by one specific asset.
- The setup-based `XAU MECH_%` location-to-asset spreadsheet produced 19,681 rows, 869 assets, and 321 unique Location values.
- The actual-results `XAU MECH_%` location-to-asset spreadsheet produced 18,723 rows, 861 assets, and 323 unique Location values.

Typical output files:

- `outputs/qa_location_values/xau_mech_location_values_by_plan_<timestamp>.csv`
- `outputs/qa_location_values/xau_mech_location_values_by_plan_<timestamp>.xlsx`
- `outputs/qa_plan_assets/xau_mech_plan_to_assets_<timestamp>.csv`
- `outputs/qa_plan_assets/xau_mech_plan_to_assets_<timestamp>.xlsx`
- `outputs/qa_plan_assets/xau_mech_plan_to_assets_from_results_<timestamp>.csv`
- `outputs/qa_plan_assets/xau_mech_plan_to_assets_from_results_<timestamp>.xlsx`
- `outputs/qa_location_assets/xau_mech_locations_to_assets_setup_<timestamp>.csv`
- `outputs/qa_location_assets/xau_mech_locations_to_assets_setup_<timestamp>.xlsx`
- `outputs/qa_location_assets/xau_mech_locations_to_assets_actual_results_<timestamp>.csv`
- `outputs/qa_location_assets/xau_mech_locations_to_assets_actual_results_<timestamp>.xlsx`

The reusable SQL patterns are documented in `sql/orcdb_sql_queries.md` under "QA Location / Asset Mapping Notes".

## Ad Hoc XAU Department Asset Group Workflow

No script in `scripts/` currently owns this report. The April 2026 lookup used a short Python snippet with `OracleDBConnector.run_query(...)`, parsed tab-delimited SQLcl output, and wrote an Excel workbook with `openpyxl`.

Source tables/views:

- `APPS.MTL_EAM_ASSET_NUMBERS_ALL_V` for asset-master rows, including `SERIAL_NUMBER`, `DESCRIPTIVE_TEXT`, `INV_ORGANIZATION_CODE`, `OWNING_DEPARTMENT`, status, area, and asset group item ID.
- `INV.MTL_SYSTEM_ITEMS_B` for the asset group item name and description, joined by `INVENTORY_ITEM_ID` and `CURRENT_ORGANIZATION_ID`.

Recommended order:

1. Resolve or filter the org with `AV.INV_ORGANIZATION_CODE = 'XAU'`.
2. Filter department codes through `AV.OWNING_DEPARTMENT IN (...)`.
3. Join to `INV.MTL_SYSTEM_ITEMS_B` to label `AV.INVENTORY_ITEM_ID` as the asset group.
4. Export one summary sheet grouped by department and asset group, plus one detail sheet with the asset rows behind each group.

Observed XAU department-code export:

- Department codes: `KAU93`, `MMABF`, `MMCBF`, `MMDFL`, `MMLFL`, `MMOWR`, `MMPKG`, `MMSBX`, `MMSHR`, `MMSRX`, `MMSSU`, `MMSTZ`, `MTU02`, `MTU90`.
- Output workbook: `outputs/xau_department_asset_groups/XAU_ALL_DEPARTMENT_CODES_ASSET_GROUP.xlsx`.
- Summary sheet contained 229 department/asset-group rows.
- Detail sheet contained 4,151 asset-master rows.

Typical output file:

- `outputs/xau_department_asset_groups/XAU_ALL_DEPARTMENT_CODES_ASSET_GROUP.xlsx`

The reusable SQL patterns are documented in `sql/orcdb_sql_queries.md` under "EAM Asset Master / Department Asset Group Notes".

## Suggested BOM/Position Pipeline

The scripts are not encoded as a single orchestrated pipeline, but the naming and dependencies imply this practical order:

1. `run_configured_boms_for_department.py` to export configured BOM CSV/XLSX files from Oracle.
2. `load_boms_to_sqlite.py` to load configured BOM CSV files into `data/BOM.db`.
3. `load_drawings_to_sqlite.py` to load the drawing workbook into `data/BOM.db`.
4. Normalize/reshape hierarchy with `create_*`, `rename_*`, `remove_*`, `rebuild_*`, and `rearrange_bom_hierarchy.py` as needed for the current schema state.
5. `create_position_table.py` and `link_drawing_to_position.py` to build and apply position mappings.
6. `create_bom_table.py` and `export_position_workbook.py` to produce the final normalized workbook.

## Inventory

| Script | Group | What it does | Inputs | Outputs |
|---|---|---|---|---|
| `backfill_drawing_hierarchy.py` | SQLite BOM/drawing maintenance | Updates `drawing` hierarchy fields from normalized asset hierarchy tables in `data/BOM.db`. Matches drawing rows to assets using cleaned asset-number keys, can skip ambiguous matches by default, and prints validation counts. | `--db data/BOM.db`, `--no-backup`, `--allow-ambiguous` | `data/BOM.db`; timestamped `.bak_YYYYMMDD_HHMMSS` backup unless disabled |
| `create_bom_hierarchy_tables.py` | SQLite BOM normalization | Creates staging hierarchy tables from `boms_for_department`, building area/department, equipment group, and asset-number style hierarchy tables for later normalization. | `--db data/BOM.db` | `data/BOM.db` |
| `create_bom_table.py` | SQLite BOM normalization | Creates the normalized `bom` table with `position_id` links. Rebuilds BOM rows from source department BOM data and removes/reshapes source columns that are no longer part of the normalized table. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `create_equipment_group_tables.py` | SQLite BOM normalization | Creates normalized equipment-group and asset-number tables from `boms_for_department`. | `--db data/BOM.db` | `data/BOM.db` |
| `create_general_asset_description.py` | SQLite BOM normalization | Derives a generalized model value from `asset_description`, removing asset tags and station/unit suffix noise, then stores the result on asset rows. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `create_general_description_table.py` | SQLite BOM normalization | Normalizes the derived model/general-description value under each asset group and rebuilds lookup relationships. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `create_position_table.py` | SQLite BOM normalization | Creates and populates the `position` table from normalized area, equipment group, model, and asset-number hierarchy tables. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `discover_configured_asset_bom.py` | Oracle discovery | Probes Oracle metadata and sample joins to confirm the configured asset BOM path. Checks objects, columns, synonyms, foreign keys, join probes, and sample configured BOM output. | No argparse flags found | `outputs/configured_asset_bom_discovery/` CSV files |
| `discover_eam_fk_relationships.py` | Oracle discovery | Discovers outbound and inbound foreign-key relationships for known EAM-related tables and exports relationship/column summaries. | No argparse flags found | `outputs/eam_fk_discovery/` style discovery outputs |
| `export_position_workbook.py` | SQLite export | Exports normalized `BOM.db` hierarchy tables to an Excel workbook with sheets for position, area, equipment group, model, asset, drawing, and chunked BOM data. | `--db data/BOM.db`, `--output data/position_load_template.xlsx` | Excel workbook at the requested output path |
| `link_drawing_to_position.py` | SQLite BOM/drawing maintenance | Adds and populates `drawing.position_id` by matching drawing rows against the normalized position mapper. Rebuilds the drawing table and prints validation counts. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `load_boms_to_sqlite.py` | SQLite load | Loads configured BOM department CSV exports into `data/BOM.db`, creating/replacing or appending to the `boms_for_department` table, adding indexes, and writing a load summary. | `--input-dir outputs/configured_boms_for_department`, `--db data/BOM.db`, `--summary-dir outputs/configured_boms_for_department`, `--chunk-size 50000`, `--append` | `data/BOM.db`; load summary CSV |
| `load_drawings_to_sqlite.py` | SQLite load | Loads the drawing workbook into the `drawing` table in `BOM.db`. Normalizes column names, matches the requested sheet, and can back up the database first. | `--db data/BOM.db`, `--workbook data/Active ...`, `--sheet ...`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `query_runner.py` | Shared Oracle report infrastructure | Central registry and runner for most small `run_*` report scripts. It parses configured arguments, substitutes SQL template tokens, runs SQLcl through `OracleDBConnector`, cleans CSV banners, and creates Excel output. | Used indirectly by wrapper scripts | `outputs/<report_name>/*.csv` and `.xlsx` |
| `rearrange_bom_hierarchy.py` | SQLite BOM normalization | Rearranges BOM hierarchy into area -> equipment group -> model/description -> asset structure, rebuilding lookup tables to match that hierarchy. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `rebuild_general_descriptions_from_parent_asset.py` | SQLite BOM normalization | Rebuilds model/general-description values for section assets from their parent `-00` asset descriptions, then rebuilds the lookup relationship. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `remove_asset_number_id.py` | SQLite schema cleanup | Removes the `asset_number_id` surrogate key from the `asset_number` table and rebuilds dependent structure as needed. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `remove_au_prefix_from_bom_db.py` | SQLite data cleanup | Removes leading `AU-` prefixes from BOM asset group and asset number values after checking duplicate risk. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `remove_general_description_from_asset_number.py` | SQLite data cleanup | Removes duplicated model/general-description text from `asset_number` values and rebuilds the affected table. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `rename_area_equipment_group.py` | SQLite schema rename | Renames older department/asset-group hierarchy naming to area/equipment-group terminology and rebuilds related hierarchy tables. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `rename_general_description_to_model.py` | SQLite schema rename | Renames the `general_description` hierarchy level to `model` and rebuilds the model lookup table. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `restore_asset_number_id_for_position.py` | SQLite schema repair | Restores `asset_number_id` and updates `position` to use that key, rebuilding related tables and validation counts. | `--db data/BOM.db`, `--no-backup` | `data/BOM.db`; timestamped backup unless disabled |
| `run_all_reports.py` | Oracle report orchestration | Runs the daily QA, 12-hour QA, and level-10 DM reports, then copies the newest generated Excel workbooks into a combined output folder. | No argparse flags found | `outputs/combined_reports/` |
| `run_asset_maintenance_burden_summary.py` | Oracle workbook report | Runs summary and detail SQL for asset maintenance burden, then builds a multi-sheet Excel workbook with asset ranking, parts, and per-asset work-order detail. Detail rows include QA plan, location, and description of work performed when available. | `--org-code XAU`, `--months 12`, `--limit 10`, `--summary-only`, `--no-parts`, `--include-time-transactions` | `outputs/asset_maintenance_burden_summary/` CSV/XLSX files |
| `run_audit_trail_full.py` | Oracle query_runner wrapper | Wrapper for `query_runner.run_named_query("audit_trail_full")`; exports user create/update audit history from a start date. | `--user-id` required, `--date-from YYYY-MM-DD` required | `outputs/audit_trail_full/` CSV/XLSX files |
| `run_audit_trail_quick.py` | Oracle query_runner wrapper | Wrapper for `audit_trail_quick`; exports quick update history for one Oracle user ID. | `--user-id` required | `outputs/audit_trail_quick/` CSV/XLSX files |
| `run_cancelled_wo_report.py` | Oracle legacy report runner | Runs `cancelled_work_orders_15_days.sql` through SQLcl and converts the CSV to Excel. | No argparse flags found | Cancelled work-order output directory from `configuration.config` |
| `run_configured_bom_for_asset.py` | Oracle query_runner wrapper | Wrapper for `configured_bom_for_asset`; exports the configured Oracle BOM for one asset. | `--org-code XAU`, `--asset-number` required, `--active-only 1` | `outputs/configured_bom_for_asset/` CSV/XLSX files |
| `run_configured_boms_for_class_code.py` | Oracle query_runner wrapper | Wrapper for `configured_boms_for_class_code`; exports configured BOMs for assets in a work-order class code. | `--org-code XAU`, `--class-code` required, `--active-only 1` | `outputs/configured_boms_for_class_code/` CSV/XLSX files |
| `run_configured_boms_for_department.py` | Oracle custom report runner | Finds PM assets for a department first, builds an inline asset CTE, then exports configured BOM rows for those assets. This avoids very large generic SQL and supports status filtering. | `--org-code XAU`, `--department-code` required, `--operation-seq 10`, `--active-only 1`, `--work-order-status Released` | `outputs/configured_boms_for_department/` CSV/XLSX files |
| `run_eam_verication.py` | Oracle verification | Runs a Python-based EAM schema/data verification suite. Checks object availability, columns, joins, known filter values, and records pass/warn/fail results. | No argparse flags found | Verification CSV/log output under `outputs` |
| `run_employees_for_resource.py` | Oracle query_runner wrapper | Wrapper for `employees_for_resource`; finds active employees assigned to a resource code. | `--org-code XAU`, `--resource-code` required | `outputs/employees_for_resource/` CSV/XLSX files |
| `run_equipment_work_po_detail.py` | Oracle query_runner wrapper | Wrapper for `equipment_work_po_detail`; exports PO detail directly linked to equipment work orders through PO distribution or requisition WIP links. This is for service/work POs tied to work orders, not the consumed-parts fallback. | `--org-code XAU`, `--months 12`, `--department-code ALL`, `--asset-number ALL`, `--split ALL` | `outputs/equipment_work_po_detail/` CSV/XLSX files |
| `run_level10_dm_report.py` | Oracle legacy report runner | Runs `level10_dm_open.sql` and converts the output to Excel for open DM work orders at operation 10. | No argparse flags found | `outputs/level10_dm_report/` style output |
| `run_lookup_user.py` | Oracle query_runner wrapper | Wrapper for `lookup_user`; looks up an Oracle user by user name, user ID, or Oracle person ID (`FND_USER.EMPLOYEE_ID`). | `--identifier` required | `outputs/lookup_user/` CSV/XLSX files |
| `run_parts_charged_to_work_order.py` | Oracle query_runner wrapper | Wrapper for `parts_charged_to_work_order`; exports part/material transactions for a work order. | `--org-code XAU`, `--work-order` required | `outputs/parts_charged_to_work_order/` CSV/XLSX files |
| `run_parts_consumption_by_asset.py` | Oracle query_runner wrapper | Wrapper for `parts_consumption_by_asset`; summarizes issued parts for one asset over a rolling month window. | `--org-code XAU`, `--asset-number` required, `--months 12` | `outputs/parts_consumption_by_asset/` CSV/XLSX files |
| `run_spare_parts_spend_detail.py` | Oracle query_runner wrapper | Wrapper for `spare_parts_spend_detail`; exports issued spare-parts spend detail for work orders over a rolling month window. Includes transaction, work order, planned/reactive split, asset, operation 10 department, part, quantity, unit material cost, and line material cost. | `--org-code XAU`, `--months 12`, `--department-code ALL`, `--asset-number ALL`, `--part-number ALL`, `--split ALL` | `outputs/spare_parts_spend_detail/` CSV/XLSX files |
| `run_person_parts_history.py` | Oracle query_runner wrapper | Wrapper for `person_parts_history`; finds work orders touched by a person through QA activity and exports parts issued to those work orders. | `--org-code XAU`, `--name` required, `--days 365` | `outputs/person_parts_history/` CSV/XLSX files |
| `run_person_wo_history.py` | Oracle query_runner wrapper | Wrapper for `person_work_order_history`; exports work orders touched/completed by a named employee. | `--org-code XAU`, `--name` required, `--days 90` | `outputs/person_work_order_history/` CSV/XLSX files |
| `run_pm_documented_hours_by_craft_month.py` | Oracle query_runner wrapper | Wrapper for `pm_documented_hours_by_craft_month`; summarizes documented/planned preventive-maintenance HR resource hours by month and craft. Uses `WIP_OPERATION_RESOURCES.USAGE_RATE_OR_AMOUNT`; craft is inferred from XAU resource code/description with unmapped-hour columns exposed for audit. | `--org-code XAU`, `--months 12` | `outputs/pm_documented_hours_by_craft_month/` CSV/XLSX files |
| `run_pm_documented_hours_by_resource_month.py` | Oracle workbook report | Builds an Excel booklet for documented/planned HR resource hours on work orders. The first sheet is a resource summary with total, planned, reactive, and monthly hours; each additional sheet contains work-order/resource-line detail for one resource. Uses `WIP_OPERATION_RESOURCES.USAGE_RATE_OR_AMOUNT` and classifies planned vs reactive from work-order type/name. | `--org-code XAU`, `--months 12` | `outputs/pm_documented_hours_by_resource_month/documented_hours_by_resource_booklet_*.xlsx` |
| `run_pm_released_wo_report.py` | Oracle legacy report runner | Runs `pm_released_work_orders.sql` and converts released PM work orders to Excel. | No argparse flags found | PM released work-order output directory from `configuration.config` |
| `run_qa_daily_report.py` | Oracle legacy report runner | Runs `qa_daily_results_24_hours.sql` and converts last-24-hour QA results to Excel. | No argparse flags found | QA daily output directory from `configuration.config` |
| `run_qa_group_members.py` | Oracle query_runner wrapper | Wrapper for `qa_group_members`; exports active members of a QA group. | `--group-name` required | `outputs/qa_group_members/` CSV/XLSX files |
| `run_qa_groups_for_user.py` | Oracle query_runner wrapper | Wrapper for `qa_groups_for_user`; exports QA groups for a user. | `--identifier` required | `outputs/qa_groups_for_user/` CSV/XLSX files |
| `run_qa_monthly_report.py` | Oracle legacy report runner | Runs `qa_results_last_31_days.sql` and converts monthly QA results to Excel. | No argparse flags found | QA monthly output directory from `configuration.config` |
| `run_qa_report_12hr.py` | Oracle legacy report runner | Runs `qa_results_last_12_hours.sql` and converts last-12-hour QA results to Excel. | No argparse flags found | QA 12-hour output directory from `configuration.config` |
| `run_qa_results_for_work_order.py` | Oracle query_runner wrapper | Wrapper for `qa_results_for_work_order`; exports QA results for one work order with technician context. | `--org-code XAU`, `--work-order` required | `outputs/qa_results_for_work_order/` CSV/XLSX files |
| `run_qa_results_with_group.py` | Oracle query_runner wrapper | Wrapper for `qa_results_with_group`; exports recent QA rows with active QA group context. | `--org-code XAU`, `--days 1` | `outputs/qa_results_with_group/` CSV/XLSX files |
| `run_released_work_orders_for_asset.py` | Oracle query_runner wrapper | Wrapper for `released_work_orders_for_asset`; lists released work orders for one asset. | `--org-code XAU`, `--asset-number` required | `outputs/released_work_orders_for_asset/` CSV/XLSX files |
| `run_resource_roster.py` | Oracle query_runner wrapper | Wrapper for `resource_roster`; exports active person-type resources and assigned employees. | `--org-code XAU` | `outputs/resource_roster/` CSV/XLSX files |
| `run_resources_for_employee.py` | Oracle query_runner wrapper | Wrapper for `resources_for_employee`; lists resources assigned to employees matching a name. | `--org-code XAU`, `--name` required | `outputs/resources_for_employee/` CSV/XLSX files |
| `run_technician_productivity_summary.py` | Oracle query_runner wrapper | Wrapper for `technician_productivity_summary`; ranks technicians by QA activity. | `--org-code XAU`, `--months 3`, `--limit 20` | `outputs/technician_productivity_summary/` CSV/XLSX files |
| `run_top_10_assets.py` | Oracle workbook report | Builds SQL from `top10_assets_wo_detail.sql`, runs it for an org code, cleans SQLcl CSV output, and formats the result workbook. | `--org-code XAU` | `outputs/top10_assets/` CSV/XLSX files |
| `run_top_assets_by_time_charged.py` | Oracle query_runner wrapper | Wrapper for `top_assets_by_time_charged`; ranks assets by actual HR time charged. | `--org-code XAU`, `--months 12`, `--limit 10` | `outputs/top_assets_by_time_charged/` CSV/XLSX files |
| `run_top_part_transactions.py` | Oracle workbook report | Runs top-part transaction summary SQL, then creates a workbook with the summary and one detail sheet per selected work order. | `--org-code XAU`, `--days 30`, `--limit 10` | `outputs/top_part_transactions/` CSV/XLSX files |
| `run_user_responsibilities_by_employee_number.py` | Oracle query_runner wrapper | Wrapper for `user_responsibilities_by_employee_number`; exports EAM responsibilities assigned to a visible HR employee number. | `--employee-number` required, `--app-short-name EAM` | `outputs/user_responsibilities_by_employee_number/` CSV/XLSX files |
| `run_user_responsibilities.py` | Oracle query_runner wrapper | Wrapper for `user_responsibilities`; exports all responsibilities assigned to one user. | `--identifier` required | `outputs/user_responsibilities/` CSV/XLSX files |
| `run_users_by_eam_responsibility.py` | Oracle query_runner wrapper | Wrapper for `users_by_responsibility`; exports active users assigned to a responsibility. | `--responsibility-name "ICU EAM Manager - XAU"`, `--app-short-name EAM` | `outputs/users_by_responsibility/` CSV/XLSX files |
| `run_verify_org_mapping.py` | Oracle query_runner wrapper | Wrapper for `verify_org_mapping`; confirms org code to organization ID mapping. | `--org-code XAU` | `outputs/verify_org_mapping/` CSV/XLSX files |
| `run_work_order_full_picture.py` | Oracle query_runner wrapper | Wrapper for `work_order_full_picture`; exports a wide work-order report with operations, QA, technician, and parts context. | `--org-code XAU`, `--work-order` required | `outputs/work_order_full_picture/` CSV/XLSX files |
| `run_work_order_operations.py` | Oracle query_runner wrapper | Wrapper for `work_order_operations`; exports operations and department details for one work order. | `--org-code XAU`, `--work-order` required | `outputs/work_order_operations/` CSV/XLSX files |
| `run_work_order_time_charged.py` | Oracle query_runner wrapper | Wrapper for `work_order_time_charged`; exports actual charged time by department/resource for a work order operation. | `--org-code XAU`, `--work-order` required, `--operation-seq 10` | `outputs/work_order_time_charged/` CSV/XLSX files |
| `run_work_order_history_planned_vs_reactive.py` | Oracle query_runner wrapper | Wrapper for `work_order_history_planned_vs_reactive`; exports rolling work-order history with each row classified as `PLANNED` or `REACTIVE`. Planned is based on PM work-order prefix or PM/preventive work-order type; everything else is treated as reactive, with a split reason column. | `--org-code XAU`, `--months 12`, `--department-code ALL`, `--asset-number ALL`, `--split ALL` | `outputs/work_order_history_planned_vs_reactive/` CSV/XLSX files |
| `run_work_orders_for_department.py` | Oracle query_runner wrapper | Wrapper for `work_orders_for_department`; exports work orders whose operation 10 department matches the requested department. | `--org-code XAU`, `--department-code` required, `--days 90` | `outputs/work_orders_for_department/` CSV/XLSX files |

## Details

### backfill_drawing_hierarchy.py

- **Group:** SQLite BOM/drawing maintenance
- **Purpose:** Updates `drawing` hierarchy fields from normalized asset hierarchy tables in `data/BOM.db`. Matches drawing rows to assets using cleaned asset-number keys, can skip ambiguous matches by default, and prints validation counts.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`, `--allow-ambiguous`
- **Outputs/side effects:** `data/BOM.db`; timestamped `.bak_YYYYMMDD_HHMMSS` backup unless disabled

### create_bom_hierarchy_tables.py

- **Group:** SQLite BOM normalization
- **Purpose:** Creates staging hierarchy tables from `boms_for_department`, building area/department, equipment group, and asset-number style hierarchy tables for later normalization.
- **Inputs/arguments:** `--db data/BOM.db`
- **Outputs/side effects:** `data/BOM.db`

### create_bom_table.py

- **Group:** SQLite BOM normalization
- **Purpose:** Creates the normalized `bom` table with `position_id` links. Rebuilds BOM rows from source department BOM data and removes/reshapes source columns that are no longer part of the normalized table.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### create_equipment_group_tables.py

- **Group:** SQLite BOM normalization
- **Purpose:** Creates normalized equipment-group and asset-number tables from `boms_for_department`.
- **Inputs/arguments:** `--db data/BOM.db`
- **Outputs/side effects:** `data/BOM.db`

### create_general_asset_description.py

- **Group:** SQLite BOM normalization
- **Purpose:** Derives a generalized model value from `asset_description`, removing asset tags and station/unit suffix noise, then stores the result on asset rows.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### create_general_description_table.py

- **Group:** SQLite BOM normalization
- **Purpose:** Normalizes the derived model/general-description value under each asset group and rebuilds lookup relationships.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### create_position_table.py

- **Group:** SQLite BOM normalization
- **Purpose:** Creates and populates the `position` table from normalized area, equipment group, model, and asset-number hierarchy tables.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### discover_configured_asset_bom.py

- **Group:** Oracle discovery
- **Purpose:** Probes Oracle metadata and sample joins to confirm the configured asset BOM path. Checks objects, columns, synonyms, foreign keys, join probes, and sample configured BOM output.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** `outputs/configured_asset_bom_discovery/` CSV files

### discover_eam_fk_relationships.py

- **Group:** Oracle discovery
- **Purpose:** Discovers outbound and inbound foreign-key relationships for known EAM-related tables and exports relationship/column summaries.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** `outputs/eam_fk_discovery/` style discovery outputs

### export_position_workbook.py

- **Group:** SQLite export
- **Purpose:** Exports normalized `BOM.db` hierarchy tables to an Excel workbook with sheets for position, area, equipment group, model, asset, drawing, and chunked BOM data.
- **Inputs/arguments:** `--db data/BOM.db`, `--output data/position_load_template.xlsx`
- **Outputs/side effects:** Excel workbook at the requested output path

### link_drawing_to_position.py

- **Group:** SQLite BOM/drawing maintenance
- **Purpose:** Adds and populates `drawing.position_id` by matching drawing rows against the normalized position mapper. Rebuilds the drawing table and prints validation counts.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### load_boms_to_sqlite.py

- **Group:** SQLite load
- **Purpose:** Loads configured BOM department CSV exports into `data/BOM.db`, creating/replacing or appending to the `boms_for_department` table, adding indexes, and writing a load summary.
- **Inputs/arguments:** `--input-dir outputs/configured_boms_for_department`, `--db data/BOM.db`, `--summary-dir outputs/configured_boms_for_department`, `--chunk-size 50000`, `--append`
- **Outputs/side effects:** `data/BOM.db`; load summary CSV

### load_drawings_to_sqlite.py

- **Group:** SQLite load
- **Purpose:** Loads the drawing workbook into the `drawing` table in `BOM.db`. Normalizes column names, matches the requested sheet, and can back up the database first.
- **Inputs/arguments:** `--db data/BOM.db`, `--workbook data/Active ...`, `--sheet ...`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### query_runner.py

- **Group:** Shared Oracle report infrastructure
- **Purpose:** Central registry and runner for most small `run_*` report scripts. It parses configured arguments, substitutes SQL template tokens, runs SQLcl through `OracleDBConnector`, cleans CSV banners, and creates Excel output.
- **Inputs/arguments:** Used indirectly by wrapper scripts
- **Outputs/side effects:** `outputs/<report_name>/*.csv` and `.xlsx`

### rearrange_bom_hierarchy.py

- **Group:** SQLite BOM normalization
- **Purpose:** Rearranges BOM hierarchy into area -> equipment group -> model/description -> asset structure, rebuilding lookup tables to match that hierarchy.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### rebuild_general_descriptions_from_parent_asset.py

- **Group:** SQLite BOM normalization
- **Purpose:** Rebuilds model/general-description values for section assets from their parent `-00` asset descriptions, then rebuilds the lookup relationship.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### remove_asset_number_id.py

- **Group:** SQLite schema cleanup
- **Purpose:** Removes the `asset_number_id` surrogate key from the `asset_number` table and rebuilds dependent structure as needed.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### remove_au_prefix_from_bom_db.py

- **Group:** SQLite data cleanup
- **Purpose:** Removes leading `AU-` prefixes from BOM asset group and asset number values after checking duplicate risk.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### remove_general_description_from_asset_number.py

- **Group:** SQLite data cleanup
- **Purpose:** Removes duplicated model/general-description text from `asset_number` values and rebuilds the affected table.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### rename_area_equipment_group.py

- **Group:** SQLite schema rename
- **Purpose:** Renames older department/asset-group hierarchy naming to area/equipment-group terminology and rebuilds related hierarchy tables.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### rename_general_description_to_model.py

- **Group:** SQLite schema rename
- **Purpose:** Renames the `general_description` hierarchy level to `model` and rebuilds the model lookup table.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### restore_asset_number_id_for_position.py

- **Group:** SQLite schema repair
- **Purpose:** Restores `asset_number_id` and updates `position` to use that key, rebuilding related tables and validation counts.
- **Inputs/arguments:** `--db data/BOM.db`, `--no-backup`
- **Outputs/side effects:** `data/BOM.db`; timestamped backup unless disabled

### run_all_reports.py

- **Group:** Oracle report orchestration
- **Purpose:** Runs the daily QA, 12-hour QA, and level-10 DM reports, then copies the newest generated Excel workbooks into a combined output folder.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** `outputs/combined_reports/`

### run_asset_maintenance_burden_summary.py

- **Group:** Oracle workbook report
- **Purpose:** Runs summary and detail SQL for asset maintenance burden, then builds a multi-sheet Excel workbook with asset ranking, parts, and per-asset work-order detail. Detail rows include QA plan, location, and description of work performed when available.
- **Inputs/arguments:** `--org-code XAU`, `--months 12`, `--limit 10`, `--summary-only`, `--no-parts`, `--include-time-transactions`
- **Outputs/side effects:** `outputs/asset_maintenance_burden_summary/` CSV/XLSX files
- **Detail QA columns:** `QA_PLAN_NAME`, `LAST_INSPECTION_DATE`, `QA_LOCATION`, `QA_DESCRIPTION_OF_WORK_PERFORMED`

### run_audit_trail_full.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `query_runner.run_named_query("audit_trail_full")`; exports user create/update audit history from a start date.
- **Inputs/arguments:** `--user-id` required, `--date-from YYYY-MM-DD` required
- **Outputs/side effects:** `outputs/audit_trail_full/` CSV/XLSX files

### run_audit_trail_quick.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `audit_trail_quick`; exports quick update history for one Oracle user ID.
- **Inputs/arguments:** `--user-id` required
- **Outputs/side effects:** `outputs/audit_trail_quick/` CSV/XLSX files

### run_cancelled_wo_report.py

- **Group:** Oracle legacy report runner
- **Purpose:** Runs `cancelled_work_orders_15_days.sql` through SQLcl and converts the CSV to Excel.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** Cancelled work-order output directory from `configuration.config`

### run_configured_bom_for_asset.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `configured_bom_for_asset`; exports the configured Oracle BOM for one asset.
- **Inputs/arguments:** `--org-code XAU`, `--asset-number` required, `--active-only 1`
- **Outputs/side effects:** `outputs/configured_bom_for_asset/` CSV/XLSX files

### run_configured_boms_for_class_code.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `configured_boms_for_class_code`; exports configured BOMs for assets in a work-order class code.
- **Inputs/arguments:** `--org-code XAU`, `--class-code` required, `--active-only 1`
- **Outputs/side effects:** `outputs/configured_boms_for_class_code/` CSV/XLSX files

### run_configured_boms_for_department.py

- **Group:** Oracle custom report runner
- **Purpose:** Finds PM assets for a department first, builds an inline asset CTE, then exports configured BOM rows for those assets. This avoids very large generic SQL and supports status filtering.
- **Inputs/arguments:** `--org-code XAU`, `--department-code` required, `--operation-seq 10`, `--active-only 1`, `--work-order-status Released`
- **Outputs/side effects:** `outputs/configured_boms_for_department/` CSV/XLSX files

### run_eam_verication.py

- **Group:** Oracle verification
- **Purpose:** Runs a Python-based EAM schema/data verification suite. Checks object availability, columns, joins, known filter values, and records pass/warn/fail results.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** Verification CSV/log output under `outputs`

### run_employees_for_resource.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `employees_for_resource`; finds active employees assigned to a resource code.
- **Inputs/arguments:** `--org-code XAU`, `--resource-code` required
- **Outputs/side effects:** `outputs/employees_for_resource/` CSV/XLSX files

### run_equipment_work_po_detail.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `equipment_work_po_detail`; exports PO detail directly linked to equipment work orders through `PO.PO_DISTRIBUTIONS_ALL.WIP_ENTITY_ID` or requisition lines with `PO.PO_REQUISITION_LINES_ALL.WIP_ENTITY_ID`. This is for service/work POs tied to work orders, not the consumed-parts fallback.
- **Inputs/arguments:** `--org-code XAU`, `--months 12`, `--department-code ALL`, `--asset-number ALL`, `--split ALL`
- **Outputs/side effects:** `outputs/equipment_work_po_detail/` CSV/XLSX files

### run_level10_dm_report.py

- **Group:** Oracle legacy report runner
- **Purpose:** Runs `level10_dm_open.sql` and converts the output to Excel for open DM work orders at operation 10.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** `outputs/level10_dm_report/` style output

### run_lookup_user.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `lookup_user`; looks up an Oracle user by user name, user ID, or Oracle person ID (`FND_USER.EMPLOYEE_ID`).
- **Inputs/arguments:** `--identifier` required
- **Outputs/side effects:** `outputs/lookup_user/` CSV/XLSX files

### run_parts_charged_to_work_order.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `parts_charged_to_work_order`; exports part/material transactions for a work order.
- **Inputs/arguments:** `--org-code XAU`, `--work-order` required
- **Outputs/side effects:** `outputs/parts_charged_to_work_order/` CSV/XLSX files

### run_parts_consumption_by_asset.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `parts_consumption_by_asset`; summarizes issued parts for one asset over a rolling month window.
- **Inputs/arguments:** `--org-code XAU`, `--asset-number` required, `--months 12`
- **Outputs/side effects:** `outputs/parts_consumption_by_asset/` CSV/XLSX files

### run_spare_parts_spend_detail.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `spare_parts_spend_detail`; exports issued spare-parts spend detail for work orders over a rolling month window. Includes transaction, work order, planned/reactive split, asset, operation 10 department, part, quantity, unit material cost, and line material cost. Material spend uses `ABS(TRANSACTION_QUANTITY) * NVL(TRANSACTION_COST, ACTUAL_COST)` for issued material transactions.
- **Inputs/arguments:** `--org-code XAU`, `--months 12`, `--department-code ALL`, `--asset-number ALL`, `--part-number ALL`, `--split ALL`
- **Outputs/side effects:** `outputs/spare_parts_spend_detail/` CSV/XLSX files

### run_person_parts_history.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `person_parts_history`; finds work orders touched by a person through QA activity and exports parts issued to those work orders.
- **Inputs/arguments:** `--org-code XAU`, `--name` required, `--days 365`
- **Outputs/side effects:** `outputs/person_parts_history/` CSV/XLSX files

### run_person_wo_history.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `person_work_order_history`; exports work orders touched/completed by a named employee.
- **Inputs/arguments:** `--org-code XAU`, `--name` required, `--days 90`
- **Outputs/side effects:** `outputs/person_work_order_history/` CSV/XLSX files

### run_pm_documented_hours_by_craft_month.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `pm_documented_hours_by_craft_month`; summarizes documented/planned preventive-maintenance HR resource hours by month and craft. Uses `WIP.WIP_OPERATION_RESOURCES.USAGE_RATE_OR_AMOUNT`; craft is inferred from XAU resource code/description. Mechanical includes maintenance, HVAC, utilities, facilities, and machine-shop style resources. Controls includes calibration, control/PLC/instrument/software/validation resources. Electrical is included only for explicit electrical resource code/description matches. Unmapped-hour columns are included for audit.
- **Inputs/arguments:** `--org-code XAU`, `--months 12`
- **Outputs/side effects:** `outputs/pm_documented_hours_by_craft_month/` CSV/XLSX files

### run_pm_documented_hours_by_resource_month.py

- **Group:** Oracle workbook report
- **Purpose:** Builds an Excel booklet for documented/planned HR resource hours on work orders. The first sheet is a resource summary with total, planned, reactive, and monthly hours; each additional sheet contains work-order/resource-line detail for one resource. Uses `WIP.WIP_OPERATION_RESOURCES.USAGE_RATE_OR_AMOUNT` and classifies planned vs reactive from work-order type/name.
- **Inputs/arguments:** `--org-code XAU`, `--months 12`
- **Outputs/side effects:** `outputs/pm_documented_hours_by_resource_month/documented_hours_by_resource_booklet_*.xlsx`

### run_pm_released_wo_report.py

- **Group:** Oracle legacy report runner
- **Purpose:** Runs `pm_released_work_orders.sql` and converts released PM work orders to Excel.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** PM released work-order output directory from `configuration.config`

### run_qa_daily_report.py

- **Group:** Oracle legacy report runner
- **Purpose:** Runs `qa_daily_results_24_hours.sql` and converts last-24-hour QA results to Excel.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** QA daily output directory from `configuration.config`

### run_qa_group_members.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `qa_group_members`; exports active members of a QA group.
- **Inputs/arguments:** `--group-name` required
- **Outputs/side effects:** `outputs/qa_group_members/` CSV/XLSX files

### run_qa_groups_for_user.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `qa_groups_for_user`; exports QA groups for a user.
- **Inputs/arguments:** `--identifier` required
- **Outputs/side effects:** `outputs/qa_groups_for_user/` CSV/XLSX files

### run_qa_monthly_report.py

- **Group:** Oracle legacy report runner
- **Purpose:** Runs `qa_results_last_31_days.sql` and converts monthly QA results to Excel.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** QA monthly output directory from `configuration.config`

### run_qa_report_12hr.py

- **Group:** Oracle legacy report runner
- **Purpose:** Runs `qa_results_last_12_hours.sql` and converts last-12-hour QA results to Excel.
- **Inputs/arguments:** No argparse flags found
- **Outputs/side effects:** QA 12-hour output directory from `configuration.config`

### run_qa_results_for_work_order.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `qa_results_for_work_order`; exports QA results for one work order with technician context.
- **Inputs/arguments:** `--org-code XAU`, `--work-order` required
- **Outputs/side effects:** `outputs/qa_results_for_work_order/` CSV/XLSX files

### run_qa_results_with_group.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `qa_results_with_group`; exports recent QA rows with active QA group context.
- **Inputs/arguments:** `--org-code XAU`, `--days 1`
- **Outputs/side effects:** `outputs/qa_results_with_group/` CSV/XLSX files

### run_released_work_orders_for_asset.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `released_work_orders_for_asset`; lists released work orders for one asset.
- **Inputs/arguments:** `--org-code XAU`, `--asset-number` required
- **Outputs/side effects:** `outputs/released_work_orders_for_asset/` CSV/XLSX files

### run_resource_roster.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `resource_roster`; exports active person-type resources and assigned employees.
- **Inputs/arguments:** `--org-code XAU`
- **Outputs/side effects:** `outputs/resource_roster/` CSV/XLSX files

### run_resources_for_employee.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `resources_for_employee`; lists resources assigned to employees matching a name.
- **Inputs/arguments:** `--org-code XAU`, `--name` required
- **Outputs/side effects:** `outputs/resources_for_employee/` CSV/XLSX files

### run_technician_productivity_summary.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `technician_productivity_summary`; ranks technicians by QA activity.
- **Inputs/arguments:** `--org-code XAU`, `--months 3`, `--limit 20`
- **Outputs/side effects:** `outputs/technician_productivity_summary/` CSV/XLSX files

### run_top_10_assets.py

- **Group:** Oracle workbook report
- **Purpose:** Builds SQL from `top10_assets_wo_detail.sql`, runs it for an org code, cleans SQLcl CSV output, and formats the result workbook.
- **Inputs/arguments:** `--org-code XAU`
- **Outputs/side effects:** `outputs/top10_assets/` CSV/XLSX files

### run_top_assets_by_time_charged.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `top_assets_by_time_charged`; ranks assets by actual HR time charged.
- **Inputs/arguments:** `--org-code XAU`, `--months 12`, `--limit 10`
- **Outputs/side effects:** `outputs/top_assets_by_time_charged/` CSV/XLSX files

### run_top_part_transactions.py

- **Group:** Oracle workbook report
- **Purpose:** Runs top-part transaction summary SQL, then creates a workbook with the summary and one detail sheet per selected work order.
- **Inputs/arguments:** `--org-code XAU`, `--days 30`, `--limit 10`
- **Outputs/side effects:** `outputs/top_part_transactions/` CSV/XLSX files

### run_user_responsibilities.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `user_responsibilities`; exports all responsibilities assigned to one user.
- **Inputs/arguments:** `--identifier` required
- **Outputs/side effects:** `outputs/user_responsibilities/` CSV/XLSX files

### run_user_responsibilities_by_employee_number.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `user_responsibilities_by_employee_number`; exports EAM responsibilities assigned to a visible HR employee number.
- **Inputs/arguments:** `--employee-number` required, `--app-short-name EAM`
- **Outputs/side effects:** `outputs/user_responsibilities_by_employee_number/` CSV/XLSX files

### run_users_by_eam_responsibility.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `users_by_responsibility`; exports active users assigned to a responsibility.
- **Inputs/arguments:** `--responsibility-name "ICU EAM Manager - XAU"`, `--app-short-name EAM`
- **Outputs/side effects:** `outputs/users_by_responsibility/` CSV/XLSX files

### run_verify_org_mapping.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `verify_org_mapping`; confirms org code to organization ID mapping.
- **Inputs/arguments:** `--org-code XAU`
- **Outputs/side effects:** `outputs/verify_org_mapping/` CSV/XLSX files

### run_work_order_full_picture.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `work_order_full_picture`; exports a wide work-order report with operations, QA, technician, and parts context.
- **Inputs/arguments:** `--org-code XAU`, `--work-order` required
- **Outputs/side effects:** `outputs/work_order_full_picture/` CSV/XLSX files

### run_work_order_operations.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `work_order_operations`; exports operations and department details for one work order.
- **Inputs/arguments:** `--org-code XAU`, `--work-order` required
- **Outputs/side effects:** `outputs/work_order_operations/` CSV/XLSX files

### run_work_order_time_charged.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `work_order_time_charged`; exports actual charged time by department/resource for a work order operation.
- **Inputs/arguments:** `--org-code XAU`, `--work-order` required, `--operation-seq 10`
- **Outputs/side effects:** `outputs/work_order_time_charged/` CSV/XLSX files

### run_work_order_history_planned_vs_reactive.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `work_order_history_planned_vs_reactive`; exports rolling work-order history with each row classified as `PLANNED` or `REACTIVE`. Planned is based on PM work-order prefix or PM/preventive work-order type; everything else is treated as reactive, with a split reason column. Includes created month, status/type, class code, asset, activity, operation 10 department, planned/applied hours, and part-use rollups.
- **Inputs/arguments:** `--org-code XAU`, `--months 12`, `--department-code ALL`, `--asset-number ALL`, `--split ALL`
- **Outputs/side effects:** `outputs/work_order_history_planned_vs_reactive/` CSV/XLSX files

### run_work_orders_for_department.py

- **Group:** Oracle query_runner wrapper
- **Purpose:** Wrapper for `work_orders_for_department`; exports work orders whose operation 10 department matches the requested department.
- **Inputs/arguments:** `--org-code XAU`, `--department-code` required, `--days 90`
- **Outputs/side effects:** `outputs/work_orders_for_department/` CSV/XLSX files
