# Oracle EAM SQL Query Reference

**Schema:** `APPS` primary, with `INV`, `BOM`, `WIP`, `EAM`, and `HR` joins where needed
**Default org context:** org `1169` / org code `XAU` unless a script exposes `__ORG_CODE__`
**Source reviewed:** all `.sql` files in `sql/`
**Last regenerated:** 2026-05-18

This reference is generated from the checked-in SQL scripts. Most scripts are SQLcl CSV exports that expect the output path as `&1` and use uppercase placeholder tokens such as `__ORG_CODE__`, `__WORK_ORDER__`, and `__DAYS__` for caller-side substitution.

## Script Inventory

| # | Script | Purpose | Complexity | Parameters |
|---|--------|---------|------------|------------|
| 1 | `asset_maintenance_burden_detail.sql` | Detailed work-order report for one asset across a rolling month window. Combines WO context, latest QA technician, QA plan/location/work-performed comments, operation 10 department, material cost, and HR time charged. | Complex | __ASSET_NUMBER__, __MONTHS__, __ORG_CODE__ |
| 2 | `asset_maintenance_burden_summary.sql` | Ranks assets by work-order volume, parts consumed, material cost, and time charged over a rolling month window. | Complex | __LIMIT__, __MONTHS__, __ORG_CODE__ |
| 3 | `audit_trail_full.sql` | Tracks created/updated activity by user across QA_RESULTS, WIP_ENTITIES, and WIP_OPERATIONS from a supplied start date. | Complex | __DATE_FROM__, __USER_ID__ |
| 4 | `audit_trail_quick.sql` | Quick user update history across QA_RESULTS, WIP_ENTITIES, and WIP_OPERATIONS without a date filter. | Complex | __USER_ID__ |
| 5 | `cancelled_work_orders_15_days.sql` | Exports recent QA rows tied to cancelled work orders for org 1169. | Medium | None |
| 6 | `configured_bom_for_asset.sql` | Returns the configured Oracle BOM for one asset using the latest asset context and common bill sequence. | Complex | __ACTIVE_ONLY__, __ASSET_NUMBER__, __ORG_CODE__ |
| 7 | `configured_boms_for_class_code.sql` | Returns configured BOM rows for assets in a class code, including latest work-order context. | Complex | __ACTIVE_ONLY__, __CLASS_CODE__, __ORG_CODE__ |
| 8 | `configured_boms_for_department.sql` | Returns configured BOM rows for released PM assets assigned to a department and optional operation sequence. | Complex | __ACTIVE_ONLY__, __DEPARTMENT_CODE__, __OPERATION_SEQ__, __ORG_CODE__ |
| 9 | `employees_for_resource.sql` | Reverse lookup from a resource code to active employees assigned to that resource. | Medium | __ORG_CODE__, __RESOURCE_CODE__ |
| 10 | `level10_dm_open.sql` | Lists open DM work orders at operation sequence 10 with assigned resource instance context. | Medium | None |
| 11 | `lookup_user.sql` | Finds an Oracle user by user name, user ID, or Oracle person ID (`FND_USER.EMPLOYEE_ID`). | Simple | __IDENTIFIER__ |
| 12 | `parts_charged_to_work_order.sql` | Lists inventory material transactions charged to a work order, including unit and line material cost. | Medium | __ORG_CODE__, __WORK_ORDER__ |
| 13 | `parts_consumption_by_asset.sql` | Summarizes parts issued to work orders for one asset over a rolling month window. | Complex | __ASSET_NUMBER__, __MONTHS__, __ORG_CODE__ |
| 14 | `person_parts_history.sql` | Uses QA activity to find work orders touched by a person, then lists issued parts for those work orders. | Complex | __DAYS__, __NAME__, __ORG_CODE__ |
| 15 | `person_work_order_history.sql` | Lists work orders completed or touched by a named employee using QA submissions over a rolling window. | Medium | __DAYS__, __NAME__, __ORG_CODE__ |
| 16 | `pm_released_work_orders.sql` | Exports currently released PM work orders for org 1169 with asset and schedule context. | Simple | None |
| 17 | `qa_daily_results_24_hours.sql` | Exports QA results from the last 24 hours with work-order and QA group context. | Medium | None |
| 18 | `qa_group_members.sql` | Lists active members of a supplied QA group. | Simple | __GROUP_NAME__ |
| 19 | `qa_groups_for_user.sql` | Lists active QA groups for a supplied user. | Simple | __IDENTIFIER__ |
| 20 | `qa_results_for_work_order.sql` | Lists QA results for one work order with technician name and badge number. | Medium | __ORG_CODE__, __WORK_ORDER__ |
| 21 | `qa_results_last_12_hours.sql` | Exports last 12 hours of AU operation 10 QA results with creator and updater names. | Medium | None |
| 22 | `qa_results_last_31_days.sql` | Exports last 31 days of AU operation 10 QA results for monthly reporting. | Medium | None |
| 23 | `qa_results_with_group.sql` | Lists recent QA results enriched with active QA group membership. | Medium | __DAYS__, __ORG_CODE__ |
| 24 | `released_work_orders_for_asset.sql` | Lists released work orders for one asset. | Simple | __ASSET_NUMBER__, __ORG_CODE__ |
| 25 | `resource_roster.sql` | Lists every active person-type resource and currently assigned employee. | Medium | __ORG_CODE__ |
| 26 | `resources_for_employee.sql` | Lists resources assigned to employees whose name matches a supplied search value. | Medium | __NAME__, __ORG_CODE__ |
| 27 | `technician_productivity_summary.sql` | Ranks technicians by QA inspection volume, distinct work orders, and distinct assets over a rolling period. | Complex | __LIMIT__, __MONTHS__, __ORG_CODE__ |
| 28 | `top_assets_by_time_charged.sql` | Ranks assets by actual HR time charged from WIP_TRANSACTIONS. | Complex | __LIMIT__, __MONTHS__, __ORG_CODE__ |
| 29 | `top_part_transactions.sql` | Finds work orders with the most part transactions in a recent rolling window. | Medium | __DAYS__, __LIMIT__, __ORG_CODE__ |
| 30 | `top_part_transactions_detail.sql` | Detail export for selected high-part-transaction work orders, including part cost and latest QA context. | Complex | __DAYS__, __ORG_CODE__, __WORK_ORDER__ |
| 31 | `top_part_transactions_summary.sql` | Summary export for top part-transaction work orders with material cost and latest QA technician context. | Complex | __DAYS__, __LIMIT__, __ORG_CODE__ |
| 32 | `top10_assets_wo_detail.sql` | Ranks assets by work-order volume and returns detailed work-order, QA, and technician context. | Complex | __ORG_CODE__ |
| 33 | `user_responsibilities.sql` | Lists responsibilities assigned to a supplied user. | Simple | __IDENTIFIER__ |
| 34 | `user_responsibilities_by_employee_number.sql` | Lists EAM responsibilities assigned to a visible HR employee number. | Medium | __APP_SHORT_NAME__, __EMPLOYEE_NUMBER__ |
| 35 | `users_by_responsibility.sql` | Lists active users assigned a supplied EAM responsibility. | Simple | __APP_SHORT_NAME__, __RESPONSIBILITY_NAME__ |
| 36 | `verify_eam_relationships.sql` | PL/SQL diagnostic script that validates expected objects, joins, filters, and data-integrity assumptions. | Diagnostic | None |
| 37 | `verify_org_mapping.sql` | Confirms the organization ID/code mapping for a supplied organization code. | Simple | __ORG_CODE__ |
| 38 | `work_order_full_picture.sql` | Wide work-order detail that combines operations, department, QA, technician, and parts transaction context. | Complex | __ORG_CODE__, __WORK_ORDER__ |
| 39 | `work_order_operations.sql` | Lists operations and department information for one work order. | Medium | __ORG_CODE__, __WORK_ORDER__ |
| 40 | `work_order_time_charged.sql` | Aggregates actual charged time for a work order and operation sequence by department and resource. | Medium | __OPERATION_SEQ__, __ORG_CODE__, __WORK_ORDER__ |
| 41 | `work_orders_for_department.sql` | Lists work orders whose operation 10 department matches a supplied department over a rolling day window. | Medium | __DAYS__, __DEPARTMENT_CODE__, __ORG_CODE__ |

## Implementation Notes

- Material cost is consistently derived from `ABS(TRANSACTION_QUANTITY) * NVL(TRANSACTION_COST, ACTUAL_COST)` where part issue cost is needed.
- Actual labor/time is sourced from `WIP.WIP_TRANSACTIONS.TRANSACTION_QUANTITY`; `WIP.WIP_OPERATION_RESOURCES.APPLIED_RESOURCE_UNITS` is used as an operation-resource rollup where included.
- Person names should join through `FND_USER.EMPLOYEE_ID -> PER_ALL_PEOPLE_F.PERSON_ID` with the effective-date filter to avoid duplicate historical person rows. Visible badge/HR employee numbers are stored as `PER_ALL_PEOPLE_F.EMPLOYEE_NUMBER`.
- Configured BOM scripts use `EAM_WORK_ORDERS_V.ASSET_GROUP_ID -> BOM_BILL_OF_MATERIALS.ASSEMBLY_ITEM_ID -> BOM_INVENTORY_COMPONENTS.BILL_SEQUENCE_ID`, reading component rows through `COMMON_BILL_SEQUENCE_ID`.
- Most report scripts are read-only exports. `verify_eam_relationships.sql` is a diagnostic PL/SQL block that writes status through `DBMS_OUTPUT`.
- Asset maintenance burden detail rows include operation 10 QA context when available: `QA_PLAN_NAME`, `LAST_INSPECTION_DATE`, `QA_LOCATION`, and `QA_DESCRIPTION_OF_WORK_PERFORMED`. For XAU mechanical plans, `Location` is commonly stored in `APPS.QA_RESULTS.CHARACTER2`, and `Description of Work Performed` is stored in `APPS.QA_RESULTS.COMMENT1`.

## EAM Asset Master / Department Asset Group Notes

There is not currently a checked-in SQL template for department asset-group exports. The April 2026 ad hoc export used `APPS.MTL_EAM_ASSET_NUMBERS_ALL_V`, which is the preferred source when the question is "which assets are in this asset group?" or "which asset groups exist for these departments?". Work-order views such as `APPS.EAM_WORK_ORDERS_V` can miss assets that do not have work-order history.

Key columns:

- `AV.INV_ORGANIZATION_CODE`: inventory org code, such as `XAU`.
- `AV.OWNING_DEPARTMENT`: asset owning department code, such as `MMLFL` or `MMABF`.
- `AV.INVENTORY_ITEM_ID`: asset group item ID.
- `AV.SERIAL_NUMBER`: asset number.
- `AV.DESCRIPTIVE_TEXT`: asset description.
- `AV.INSTANCE_STATUS` / `AV.CURRENT_STATUS_MEANING`: asset status fields.
- `INV.MTL_SYSTEM_ITEMS_B.SEGMENT1`: asset group item name.
- `INV.MTL_SYSTEM_ITEMS_B.DESCRIPTION`: asset group description.

### Asset groups by department

Use this summary query when the request is all asset groups represented in one org and a list of owning department codes. Replace `__ORG_CODE__` and the department-code list before running. The `DEPARTMENT_SORT` case expression is optional, but it preserves a user-supplied department order in the spreadsheet.

```sql
SELECT
    AV.OWNING_DEPARTMENT AS DEPARTMENT_CODE,
    CASE AV.OWNING_DEPARTMENT
        WHEN 'KAU93' THEN 1
        WHEN 'MMABF' THEN 2
        WHEN 'MMCBF' THEN 3
        WHEN 'MMDFL' THEN 4
        WHEN 'MMLFL' THEN 5
        WHEN 'MMOWR' THEN 6
        WHEN 'MMPKG' THEN 7
        WHEN 'MMSBX' THEN 8
        WHEN 'MMSHR' THEN 9
        WHEN 'MMSRX' THEN 10
        WHEN 'MMSSU' THEN 11
        WHEN 'MMSTZ' THEN 12
        WHEN 'MTU02' THEN 13
        WHEN 'MTU90' THEN 14
        ELSE 999
    END AS DEPARTMENT_SORT,
    NVL(AG.SEGMENT1, TO_CHAR(AV.INVENTORY_ITEM_ID)) AS ASSET_GROUP,
    AV.INVENTORY_ITEM_ID AS ASSET_GROUP_ID,
    NVL(AG.DESCRIPTION, AV.ASSET_GROUP_DESCRIPTION) AS ASSET_GROUP_DESCRIPTION,
    COUNT(*) AS ASSET_COUNT,
    SUM(CASE WHEN UPPER(NVL(AV.INSTANCE_STATUS, AV.CURRENT_STATUS_MEANING)) = 'CREATED' THEN 1 ELSE 0 END) AS CREATED_COUNT,
    SUM(CASE WHEN UPPER(NVL(AV.INSTANCE_STATUS, AV.CURRENT_STATUS_MEANING)) = 'EXPIRED' THEN 1 ELSE 0 END) AS EXPIRED_COUNT
FROM APPS.MTL_EAM_ASSET_NUMBERS_ALL_V AV
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B AG
    ON AG.INVENTORY_ITEM_ID = AV.INVENTORY_ITEM_ID
   AND AG.ORGANIZATION_ID = AV.CURRENT_ORGANIZATION_ID
WHERE AV.INV_ORGANIZATION_CODE = __ORG_CODE__
  AND AV.OWNING_DEPARTMENT IN (
      'KAU93', 'MMABF', 'MMCBF', 'MMDFL', 'MMLFL', 'MMOWR', 'MMPKG',
      'MMSBX', 'MMSHR', 'MMSRX', 'MMSSU', 'MMSTZ', 'MTU02', 'MTU90'
  )
  AND AV.INVENTORY_ITEM_ID IS NOT NULL
GROUP BY
    AV.OWNING_DEPARTMENT,
    CASE AV.OWNING_DEPARTMENT
        WHEN 'KAU93' THEN 1
        WHEN 'MMABF' THEN 2
        WHEN 'MMCBF' THEN 3
        WHEN 'MMDFL' THEN 4
        WHEN 'MMLFL' THEN 5
        WHEN 'MMOWR' THEN 6
        WHEN 'MMPKG' THEN 7
        WHEN 'MMSBX' THEN 8
        WHEN 'MMSHR' THEN 9
        WHEN 'MMSRX' THEN 10
        WHEN 'MMSSU' THEN 11
        WHEN 'MMSTZ' THEN 12
        WHEN 'MTU02' THEN 13
        WHEN 'MTU90' THEN 14
        ELSE 999
    END,
    NVL(AG.SEGMENT1, TO_CHAR(AV.INVENTORY_ITEM_ID)),
    AV.INVENTORY_ITEM_ID,
    NVL(AG.DESCRIPTION, AV.ASSET_GROUP_DESCRIPTION)
ORDER BY
    DEPARTMENT_SORT,
    ASSET_GROUP;
```

### Asset detail behind department asset groups

Use this detail query for the second workbook sheet. It returns one asset-master row per asset, sorted by department order, asset group, and asset number.

```sql
SELECT
    AV.OWNING_DEPARTMENT AS DEPARTMENT_CODE,
    CASE AV.OWNING_DEPARTMENT
        WHEN 'KAU93' THEN 1
        WHEN 'MMABF' THEN 2
        WHEN 'MMCBF' THEN 3
        WHEN 'MMDFL' THEN 4
        WHEN 'MMLFL' THEN 5
        WHEN 'MMOWR' THEN 6
        WHEN 'MMPKG' THEN 7
        WHEN 'MMSBX' THEN 8
        WHEN 'MMSHR' THEN 9
        WHEN 'MMSRX' THEN 10
        WHEN 'MMSSU' THEN 11
        WHEN 'MMSTZ' THEN 12
        WHEN 'MTU02' THEN 13
        WHEN 'MTU90' THEN 14
        ELSE 999
    END AS DEPARTMENT_SORT,
    NVL(AG.SEGMENT1, TO_CHAR(AV.INVENTORY_ITEM_ID)) AS ASSET_GROUP,
    AV.INVENTORY_ITEM_ID AS ASSET_GROUP_ID,
    NVL(AG.DESCRIPTION, AV.ASSET_GROUP_DESCRIPTION) AS ASSET_GROUP_DESCRIPTION,
    AV.SERIAL_NUMBER AS ASSET_NUMBER,
    AV.DESCRIPTIVE_TEXT AS ASSET_DESCRIPTION,
    AV.AREA,
    AV.INSTANCE_STATUS,
    AV.CURRENT_STATUS_MEANING,
    AV.MAINTAINABLE_FLAG,
    AV.CATEGORY_NAME,
    AV.ASSET_CRITICALITY,
    AV.CURRENT_SUBINVENTORY_CODE,
    AV.INSTANCE_NUMBER,
    AV.MAINTENANCE_OBJECT_ID,
    TO_CHAR(AV.ACTIVE_START_DATE, 'YYYY-MM-DD') AS ACTIVE_START_DATE,
    TO_CHAR(AV.ACTIVE_END_DATE, 'YYYY-MM-DD') AS ACTIVE_END_DATE,
    TO_CHAR(AV.CREATION_DATE, 'YYYY-MM-DD HH24:MI:SS') AS CREATION_DATE,
    TO_CHAR(AV.LAST_UPDATE_DATE, 'YYYY-MM-DD HH24:MI:SS') AS LAST_UPDATE_DATE
FROM APPS.MTL_EAM_ASSET_NUMBERS_ALL_V AV
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B AG
    ON AG.INVENTORY_ITEM_ID = AV.INVENTORY_ITEM_ID
   AND AG.ORGANIZATION_ID = AV.CURRENT_ORGANIZATION_ID
WHERE AV.INV_ORGANIZATION_CODE = __ORG_CODE__
  AND AV.OWNING_DEPARTMENT IN (
      'KAU93', 'MMABF', 'MMCBF', 'MMDFL', 'MMLFL', 'MMOWR', 'MMPKG',
      'MMSBX', 'MMSHR', 'MMSRX', 'MMSSU', 'MMSTZ', 'MTU02', 'MTU90'
  )
  AND AV.INVENTORY_ITEM_ID IS NOT NULL
ORDER BY
    DEPARTMENT_SORT,
    ASSET_GROUP,
    AV.SERIAL_NUMBER;
```

### One asset group by org

Use this narrower form when the request is all assets in one asset group, for example `LIFECARE_FILLING` or `ADDVANTAGE_BAG_FABRICATION`, optionally constrained to one org and department list.

```sql
SELECT
    AV.INV_ORGANIZATION_CODE AS ORG_CODE,
    AV.CURRENT_ORGANIZATION_ID AS ORGANIZATION_ID,
    AG.SEGMENT1 AS ASSET_GROUP,
    AV.INVENTORY_ITEM_ID AS ASSET_GROUP_ID,
    AV.SERIAL_NUMBER AS ASSET_NUMBER,
    AV.DESCRIPTIVE_TEXT AS ASSET_DESCRIPTION,
    AV.OWNING_DEPARTMENT,
    AV.AREA,
    AV.INSTANCE_STATUS,
    AV.CURRENT_STATUS_MEANING,
    AV.MAINTAINABLE_FLAG,
    AV.CATEGORY_NAME,
    AV.ASSET_CRITICALITY,
    AV.CURRENT_SUBINVENTORY_CODE,
    AV.INSTANCE_NUMBER,
    AV.MAINTENANCE_OBJECT_ID,
    TO_CHAR(AV.ACTIVE_START_DATE, 'YYYY-MM-DD') AS ACTIVE_START_DATE,
    TO_CHAR(AV.ACTIVE_END_DATE, 'YYYY-MM-DD') AS ACTIVE_END_DATE,
    TO_CHAR(AV.CREATION_DATE, 'YYYY-MM-DD HH24:MI:SS') AS CREATION_DATE,
    TO_CHAR(AV.LAST_UPDATE_DATE, 'YYYY-MM-DD HH24:MI:SS') AS LAST_UPDATE_DATE
FROM APPS.MTL_EAM_ASSET_NUMBERS_ALL_V AV
JOIN INV.MTL_SYSTEM_ITEMS_B AG
    ON AG.INVENTORY_ITEM_ID = AV.INVENTORY_ITEM_ID
   AND AG.ORGANIZATION_ID = AV.CURRENT_ORGANIZATION_ID
WHERE AV.INV_ORGANIZATION_CODE = __ORG_CODE__
  AND UPPER(AG.SEGMENT1) = UPPER(__ASSET_GROUP__)
  -- Optional department filter:
  -- AND AV.OWNING_DEPARTMENT IN ('MMLFL', 'MMABF')
ORDER BY
    AV.SERIAL_NUMBER;
```

## Purchasing / PO Lookup Notes

There is not currently a checked-in SQL template for asset PO history. The April 2026 ad hoc lookup used two paths:

1. Direct PO/requisition links to the asset work order.
2. Fallback PO history for parts consumed on the asset in the last 12 months.

The direct path is worth checking first, but it can legitimately return no rows. For example, `AU-ACS7100-00` had 1,932 work orders in `XAU`, but no all-time matches through either `PO.PO_DISTRIBUTIONS_ALL.WIP_ENTITY_ID` or `PO.PO_REQUISITION_LINES_ALL.WIP_ENTITY_ID`.

### Direct PO links from asset work orders

Use this when the PO distribution is charged directly to the eAM/WIP work order:

```sql
WITH ASSET_WOS AS (
    SELECT
        EWO.ORGANIZATION_ID,
        EWO.WIP_ENTITY_ID,
        EWO.WIP_ENTITY_NAME AS WORK_ORDER,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
)
SELECT
    AW.ASSET_NUMBER,
    AW.ASSET_DESCRIPTION,
    AW.WORK_ORDER,
    POH.SEGMENT1 AS PO_NUMBER,
    POH.AUTHORIZATION_STATUS AS PO_STATUS,
    TO_CHAR(POH.CREATION_DATE, 'MM/DD/YYYY') AS PO_CREATED,
    APS.VENDOR_NAME AS SUPPLIER_NAME,
    POL.LINE_NUM AS PO_LINE_NUM,
    COALESCE(MSI.DESCRIPTION, POL.ITEM_DESCRIPTION) AS ITEM_DESCRIPTION,
    POL.UNIT_PRICE,
    POD.QUANTITY_ORDERED,
    POD.QUANTITY_DELIVERED,
    POD.QUANTITY_BILLED,
    POD.AMOUNT_ORDERED,
    POD.PO_DISTRIBUTION_ID
FROM ASSET_WOS AW
JOIN PO.PO_DISTRIBUTIONS_ALL POD
    ON POD.WIP_ENTITY_ID = AW.WIP_ENTITY_ID
   AND POD.DESTINATION_ORGANIZATION_ID = AW.ORGANIZATION_ID
JOIN PO.PO_HEADERS_ALL POH
    ON POH.PO_HEADER_ID = POD.PO_HEADER_ID
JOIN PO.PO_LINES_ALL POL
    ON POL.PO_LINE_ID = POD.PO_LINE_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B MSI
    ON MSI.INVENTORY_ITEM_ID = POL.ITEM_ID
   AND MSI.ORGANIZATION_ID = AW.ORGANIZATION_ID
LEFT JOIN APPS.AP_SUPPLIERS APS
    ON APS.VENDOR_ID = POH.VENDOR_ID
WHERE POH.CREATION_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -__MONTHS__)
ORDER BY POH.CREATION_DATE DESC, POH.SEGMENT1, POL.LINE_NUM, POD.PO_DISTRIBUTION_ID;
```

### PO history for parts consumed on an asset

Use this fallback when the asset work orders have material issues but no direct PO links. It finds parts issued to the asset in the rolling window, then returns PO lines for those same inventory items in the same org and date window.

```sql
WITH PART_USAGE AS (
    SELECT
        EWO.ORGANIZATION_ID,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        MMT.INVENTORY_ITEM_ID,
        MSI.SEGMENT1 AS PART_NUMBER,
        MSI.DESCRIPTION AS PART_DESCRIPTION,
        MMT.TRANSACTION_UOM AS USAGE_UOM,
        COUNT(*) AS ASSET_ISSUE_COUNT,
        SUM(ABS(MMT.TRANSACTION_QUANTITY)) AS ASSET_QTY_USED,
        SUM(ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST)) AS ASSET_MATERIAL_COST,
        MIN(MMT.TRANSACTION_DATE) AS FIRST_ASSET_USAGE_DATE,
        MAX(MMT.TRANSACTION_DATE) AS LAST_ASSET_USAGE_DATE
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
        ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
       AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
       AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
       AND MMT.TRANSACTION_QUANTITY < 0
    JOIN INV.MTL_SYSTEM_ITEMS_B MSI
        ON MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
       AND MSI.ORGANIZATION_ID = MMT.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
      AND MMT.TRANSACTION_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -__MONTHS__)
    GROUP BY
        EWO.ORGANIZATION_ID,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        MMT.INVENTORY_ITEM_ID,
        MSI.SEGMENT1,
        MSI.DESCRIPTION,
        MMT.TRANSACTION_UOM
)
SELECT
    PU.ASSET_NUMBER,
    PU.ASSET_DESCRIPTION,
    PU.PART_NUMBER,
    PU.PART_DESCRIPTION,
    PU.ASSET_ISSUE_COUNT,
    PU.ASSET_QTY_USED,
    PU.USAGE_UOM,
    PU.ASSET_MATERIAL_COST,
    TO_CHAR(PU.FIRST_ASSET_USAGE_DATE, 'MM/DD/YYYY') AS FIRST_ASSET_USAGE_DATE,
    TO_CHAR(PU.LAST_ASSET_USAGE_DATE, 'MM/DD/YYYY') AS LAST_ASSET_USAGE_DATE,
    POH.SEGMENT1 AS PO_NUMBER,
    POH.AUTHORIZATION_STATUS AS PO_STATUS,
    TO_CHAR(POH.CREATION_DATE, 'MM/DD/YYYY') AS PO_CREATED,
    APS.VENDOR_NAME AS SUPPLIER_NAME,
    POL.LINE_NUM AS PO_LINE_NUM,
    POL.ITEM_DESCRIPTION AS PO_LINE_DESCRIPTION,
    POL.UNIT_MEAS_LOOKUP_CODE AS PO_UOM,
    POL.UNIT_PRICE,
    POD.QUANTITY_ORDERED,
    POD.QUANTITY_DELIVERED,
    POD.QUANTITY_BILLED,
    POD.AMOUNT_ORDERED,
    POD.PO_DISTRIBUTION_ID
FROM PART_USAGE PU
JOIN PO.PO_LINES_ALL POL
    ON POL.ITEM_ID = PU.INVENTORY_ITEM_ID
JOIN PO.PO_HEADERS_ALL POH
    ON POH.PO_HEADER_ID = POL.PO_HEADER_ID
JOIN PO.PO_DISTRIBUTIONS_ALL POD
    ON POD.PO_LINE_ID = POL.PO_LINE_ID
   AND POD.DESTINATION_ORGANIZATION_ID = PU.ORGANIZATION_ID
LEFT JOIN APPS.AP_SUPPLIERS APS
    ON APS.VENDOR_ID = POH.VENDOR_ID
WHERE POH.CREATION_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -__MONTHS__)
ORDER BY POH.CREATION_DATE DESC, POH.SEGMENT1, POL.LINE_NUM, PU.PART_NUMBER, POD.PO_DISTRIBUTION_ID;
```

## QA Location / Asset Mapping Notes

There is not currently a checked-in SQL template for QA location-to-asset mapping. The April 2026 ad hoc lookup was built from Oracle Quality setup tables and EAM work-order history.

For XAU mechanical EAM completion screens, the user-facing `Location` field is a QA collection element:

- Collection plan setup: `QA.QA_PLANS`
- Plan fields/prompts: `QA.QA_PLAN_CHARS`
- Master element metadata: `QA.QA_CHARS`
- Plan-specific selectable values: `QA.QA_PLAN_CHAR_VALUE_LOOKUPS`
- Plan collection triggers: `APPS.QA_PLAN_COLLECTION_TRIGGERS_V`
- Submitted result values: `APPS.QA_RESULTS`

For the example work order `AU14947817`, plan `XAU MECH_FILLING PF` maps `Location` to `QA_RESULTS.CHARACTER2`:

```sql
SELECT
    QP.PLAN_ID,
    QP.NAME AS PLAN_NAME,
    QPC.CHAR_ID,
    QC.NAME AS ELEMENT_NAME,
    QPC.PROMPT,
    QPC.RESULT_COLUMN_NAME,
    QPC.PROMPT_SEQUENCE
FROM QA.QA_PLANS QP
JOIN QA.QA_PLAN_CHARS QPC
    ON QPC.PLAN_ID = QP.PLAN_ID
JOIN QA.QA_CHARS QC
    ON QC.CHAR_ID = QPC.CHAR_ID
WHERE QP.NAME = 'XAU MECH_FILLING PF'
  AND UPPER(QPC.PROMPT) = 'LOCATION';
```

### Location values by QA plan

This returns the selectable `Location` values and the plan/element they are tied to:

```sql
SELECT DISTINCT
    MP.ORGANIZATION_CODE,
    QP.PLAN_ID,
    QP.NAME AS PLAN_NAME,
    QP.DESCRIPTION AS PLAN_DESCRIPTION,
    QPC.CHAR_ID,
    QC.NAME AS ELEMENT_NAME,
    QPC.PROMPT AS FIELD_PROMPT,
    QPC.RESULT_COLUMN_NAME,
    QPCVL.SHORT_CODE AS LOCATION_VALUE,
    QPCVL.DESCRIPTION AS LOCATION_DESCRIPTION
FROM QA.QA_PLANS QP
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = QP.ORGANIZATION_ID
JOIN QA.QA_PLAN_CHARS QPC
    ON QPC.PLAN_ID = QP.PLAN_ID
JOIN QA.QA_CHARS QC
    ON QC.CHAR_ID = QPC.CHAR_ID
JOIN QA.QA_PLAN_CHAR_VALUE_LOOKUPS QPCVL
    ON QPCVL.PLAN_ID = QPC.PLAN_ID
   AND QPCVL.CHAR_ID = QPC.CHAR_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND QP.NAME LIKE __PLAN_NAME_LIKE__
  AND UPPER(QPC.PROMPT) = 'LOCATION'
  AND QPC.ENABLED_FLAG = 1
ORDER BY QP.NAME, QPCVL.SHORT_CODE;
```

For XAU EAM mechanical plans, use `__ORG_CODE__ = 'XAU'` and `__PLAN_NAME_LIKE__ = 'XAU MECH_%'`.

### Setup-based locations tied to assets

This is the preferred report when the goal is: "which locations can an asset select from on the Data screen?" It maps:

`QA plan -> Asset Activity trigger -> EAM assets with work orders using that activity -> plan Location values`

```sql
WITH PLAN_ACTIVITY AS (
    SELECT DISTINCT
        QP.PLAN_ID,
        QP.NAME AS PLAN_NAME,
        QP.DESCRIPTION AS PLAN_DESCRIPTION,
        MP.ORGANIZATION_CODE,
        QPCT.LOW_VALUE AS ASSET_ACTIVITY,
        QPCT.LOW_VALUE_ID AS ASSET_ACTIVITY_ID
    FROM QA.QA_PLANS QP
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = QP.ORGANIZATION_ID
    JOIN APPS.QA_PLAN_COLLECTION_TRIGGERS_V QPCT
        ON QPCT.PLAN_ID = QP.PLAN_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND QP.NAME LIKE __PLAN_NAME_LIKE__
      AND QPCT.COLLECTION_TRIGGER_DESCRIPTION = 'Asset Activity'
      AND QPCT.OPERATOR_MEANING = 'equals'
), PLAN_LOCATIONS AS (
    SELECT DISTINCT
        QP.PLAN_ID,
        QPC.CHAR_ID,
        QC.NAME AS ELEMENT_NAME,
        QPC.PROMPT AS FIELD_PROMPT,
        QPC.RESULT_COLUMN_NAME,
        QPCVL.SHORT_CODE AS LOCATION_VALUE,
        QPCVL.DESCRIPTION AS LOCATION_DESCRIPTION
    FROM QA.QA_PLANS QP
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = QP.ORGANIZATION_ID
    JOIN QA.QA_PLAN_CHARS QPC
        ON QPC.PLAN_ID = QP.PLAN_ID
    JOIN QA.QA_CHARS QC
        ON QC.CHAR_ID = QPC.CHAR_ID
    JOIN QA.QA_PLAN_CHAR_VALUE_LOOKUPS QPCVL
        ON QPCVL.PLAN_ID = QPC.PLAN_ID
       AND QPCVL.CHAR_ID = QPC.CHAR_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND QP.NAME LIKE __PLAN_NAME_LIKE__
      AND UPPER(QPC.PROMPT) = 'LOCATION'
      AND QPC.ENABLED_FLAG = 1
), PLAN_ASSETS AS (
    SELECT
        PA.ORGANIZATION_CODE,
        PA.PLAN_ID,
        PA.PLAN_NAME,
        PA.PLAN_DESCRIPTION,
        PA.ASSET_ACTIVITY,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        EWO.ASSET_GROUP_ID,
        COUNT(DISTINCT EWO.WIP_ENTITY_ID) AS WORK_ORDER_COUNT_ALL_TIME,
        SUM(CASE WHEN EWO.CREATION_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -12) THEN 1 ELSE 0 END) AS WORK_ORDER_COUNT_12MO,
        MIN(EWO.CREATION_DATE) AS FIRST_WORK_ORDER_DATE,
        MAX(EWO.CREATION_DATE) AS LAST_WORK_ORDER_DATE
    FROM PLAN_ACTIVITY PA
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.ASSET_ACTIVITY = PA.ASSET_ACTIVITY
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
       AND MP.ORGANIZATION_CODE = PA.ORGANIZATION_CODE
    WHERE EWO.ASSET_NUMBER IS NOT NULL
    GROUP BY
        PA.ORGANIZATION_CODE,
        PA.PLAN_ID,
        PA.PLAN_NAME,
        PA.PLAN_DESCRIPTION,
        PA.ASSET_ACTIVITY,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        EWO.ASSET_GROUP_ID
)
SELECT
    PA.ORGANIZATION_CODE,
    PA.ASSET_NUMBER,
    PA.ASSET_DESCRIPTION,
    PA.ASSET_ACTIVITY,
    PA.PLAN_ID,
    PA.PLAN_NAME,
    PL.LOCATION_VALUE,
    PL.LOCATION_DESCRIPTION,
    PL.RESULT_COLUMN_NAME,
    PA.WORK_ORDER_COUNT_ALL_TIME,
    PA.WORK_ORDER_COUNT_12MO,
    TO_CHAR(PA.FIRST_WORK_ORDER_DATE, 'MM/DD/YYYY') AS FIRST_WORK_ORDER_DATE,
    TO_CHAR(PA.LAST_WORK_ORDER_DATE, 'MM/DD/YYYY') AS LAST_WORK_ORDER_DATE
FROM PLAN_ASSETS PA
JOIN PLAN_LOCATIONS PL
    ON PL.PLAN_ID = PA.PLAN_ID
ORDER BY PA.ASSET_NUMBER, PA.PLAN_NAME, PL.LOCATION_VALUE;
```

### Actual submitted QA locations tied to assets

Use `APPS.QA_RESULTS` when the goal is to see assets that have actually had QA results submitted under a plan. For XAU mechanical plans, saved `Location` values commonly appear in `CHARACTER2`, but the safer general mapping is to read `QA_PLAN_CHARS.RESULT_COLUMN_NAME` for the plan field.

```sql
SELECT
    MP.ORGANIZATION_CODE,
    QP.PLAN_ID,
    QP.NAME AS PLAN_NAME,
    EWO.ASSET_ACTIVITY,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    COUNT(DISTINCT QR.OCCURRENCE) AS QA_RESULT_COUNT_ALL_TIME,
    SUM(CASE WHEN QR.QA_CREATION_DATE >= ADD_MONTHS(TRUNC(SYSDATE), -12) THEN 1 ELSE 0 END) AS QA_RESULT_COUNT_12MO,
    MIN(QR.QA_CREATION_DATE) AS FIRST_QA_RESULT_DATE,
    MAX(QR.QA_CREATION_DATE) AS LAST_QA_RESULT_DATE
FROM APPS.QA_RESULTS QR
JOIN QA.QA_PLANS QP
    ON QP.PLAN_ID = QR.PLAN_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = QR.ORGANIZATION_ID
LEFT JOIN APPS.EAM_WORK_ORDERS_V EWO
    ON EWO.ORGANIZATION_ID = QR.ORGANIZATION_ID
   AND EWO.WIP_ENTITY_ID = QR.WORK_ORDER_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND QP.NAME LIKE __PLAN_NAME_LIKE__
  AND EWO.ASSET_NUMBER IS NOT NULL
GROUP BY
    MP.ORGANIZATION_CODE,
    QP.PLAN_ID,
    QP.NAME,
    EWO.ASSET_ACTIVITY,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION
ORDER BY QP.NAME, EWO.ASSET_NUMBER;
```

## Scripts

### 1. Asset maintenance burden detail

**File:** `sql/asset_maintenance_burden_detail.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Detailed work-order report for one asset across a rolling month window. Combines WO context, latest QA technician, QA plan/location/work-performed comments, operation 10 department, material cost, and HR time charged.
**Parameters:** __ASSET_NUMBER__, __MONTHS__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS, APPS.WIP_OPERATIONS_V, BOM.BOM_DEPARTMENTS, BOM.BOM_RESOURCES, INV.MTL_MATERIAL_TRANSACTIONS, QA.QA_PLANS, WIP.WIP_TRANSACTIONS

**QA result columns added to work-order rows:** `QA_PLAN_NAME`, `LAST_INSPECTION_DATE`, `QA_LOCATION`, `QA_DESCRIPTION_OF_WORK_PERFORMED`

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH LATEST_QA AS (
    SELECT
        QR.ORGANIZATION_ID,
        QR.WORK_ORDER_ID,
        PEO.FULL_NAME AS TECHNICIAN,
        FU.USER_NAME AS BADGE_NUMBER,
        TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS LAST_INSPECTION_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY QR.ORGANIZATION_ID, QR.WORK_ORDER_ID
            ORDER BY QR.QA_CREATION_DATE DESC
        ) AS RN
    FROM APPS.QA_RESULTS QR
    LEFT JOIN APPS.FND_USER FU
        ON FU.USER_ID = QR.QA_CREATED_BY
    LEFT JOIN APPS.PER_ALL_PEOPLE_F PEO
        ON PEO.PERSON_ID = FU.EMPLOYEE_ID
       AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
),
WO_PARTS AS (
    SELECT
        EWO.ORGANIZATION_ID,
        EWO.WIP_ENTITY_ID,
        COUNT(MMT.TRANSACTION_ID) AS PART_TRANSACTION_COUNT,
        COUNT(DISTINCT MMT.INVENTORY_ITEM_ID) AS DISTINCT_PARTS_USED,
        SUM(ABS(MMT.TRANSACTION_QUANTITY)) AS TOTAL_PARTS_CONSUMED,
        SUM(ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST)) AS TOTAL_MATERIAL_COST
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
        ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
       AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
       AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
       AND MMT.TRANSACTION_QUANTITY < 0
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
      AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
    GROUP BY EWO.ORGANIZATION_ID, EWO.WIP_ENTITY_ID
),
WO_TIME AS (
    SELECT
        EWO.ORGANIZATION_ID,
        EWO.WIP_ENTITY_ID,
        COUNT(DISTINCT TO_CHAR(WT.OPERATION_SEQ_NUM) || ':' || TO_CHAR(WT.RESOURCE_SEQ_NUM)) AS RESOURCE_LINE_COUNT,
        COUNT(WT.ROWID) AS TIME_TRANSACTION_COUNT,
        SUM(WT.TRANSACTION_QUANTITY) AS TOTAL_TIME_CHARGED_HOURS,
        SUM(CASE WHEN WT.OPERATION_SEQ_NUM = 10 THEN WT.TRANSACTION_QUANTITY ELSE 0 END) AS OP10_TIME_CHARGED_HOURS
    FROM WIP.WIP_TRANSACTIONS WT
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.WIP_ENTITY_ID = WT.WIP_ENTITY_ID
       AND EWO.ORGANIZATION_ID = WT.ORGANIZATION_ID
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    LEFT JOIN BOM.BOM_RESOURCES BR
        ON BR.RESOURCE_ID = WT.RESOURCE_ID
       AND BR.ORGANIZATION_ID = WT.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
      AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
      AND BR.UNIT_OF_MEASURE = 'HR'
    GROUP BY EWO.ORGANIZATION_ID, EWO.WIP_ENTITY_ID
),
OP10_DEPT AS (
    SELECT
        WO.ORGANIZATION_ID,
        WO.WIP_ENTITY_ID,
        BD.DEPARTMENT_CODE AS PRIMARY_DEPARTMENT_CODE,
        BD.DESCRIPTION AS PRIMARY_DEPARTMENT_DESCRIPTION
    FROM APPS.WIP_OPERATIONS_V WO
    LEFT JOIN BOM.BOM_DEPARTMENTS BD
        ON BD.DEPARTMENT_ID = WO.DEPARTMENT_ID
       AND BD.ORGANIZATION_ID = WO.ORGANIZATION_ID
    WHERE WO.OPERATION_SEQ_NUM = 10
)
SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP AS WO_TYPE,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    EWO.ASSET_ACTIVITY,
    EWO.DESCRIPTION AS WO_DESCRIPTION,
    TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS WO_CREATED,
    TO_CHAR(EWO.SCHEDULED_START_DATE, 'MM/DD/YYYY') AS SCHEDULED_START,
    OP10.PRIMARY_DEPARTMENT_CODE,
    OP10.PRIMARY_DEPARTMENT_DESCRIPTION,
    LQ.TECHNICIAN,
    LQ.BADGE_NUMBER,
    LQ.LAST_INSPECTION_DATE,
    NVL(WT.RESOURCE_LINE_COUNT, 0) AS RESOURCE_LINE_COUNT,
    NVL(WT.TIME_TRANSACTION_COUNT, 0) AS TIME_TRANSACTION_COUNT,
    NVL(WT.OP10_TIME_CHARGED_HOURS, 0) AS OP10_TIME_CHARGED_HOURS,
    NVL(WT.TOTAL_TIME_CHARGED_HOURS, 0) AS TOTAL_TIME_CHARGED_HOURS,
    NVL(WP.PART_TRANSACTION_COUNT, 0) AS PART_TRANSACTION_COUNT,
    NVL(WP.DISTINCT_PARTS_USED, 0) AS DISTINCT_PARTS_USED,
    NVL(WP.TOTAL_PARTS_CONSUMED, 0) AS TOTAL_PARTS_CONSUMED,
    NVL(WP.TOTAL_MATERIAL_COST, 0) AS TOTAL_MATERIAL_COST
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
LEFT JOIN LATEST_QA LQ
    ON LQ.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND LQ.WORK_ORDER_ID = EWO.WIP_ENTITY_ID
   AND LQ.RN = 1
LEFT JOIN WO_PARTS WP
    ON WP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND WP.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
LEFT JOIN WO_TIME WT
    ON WT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND WT.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
LEFT JOIN OP10_DEPT OP10
    ON OP10.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND OP10.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
  AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
ORDER BY EWO.CREATION_DATE DESC, EWO.WIP_ENTITY_NAME DESC;
```

### 2. Asset maintenance burden summary

**File:** `sql/asset_maintenance_burden_summary.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Ranks assets by work-order volume, parts consumed, material cost, and time charged over a rolling month window.
**Parameters:** __LIMIT__, __MONTHS__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, BOM.BOM_RESOURCES, INV.MTL_MATERIAL_TRANSACTIONS, WIP.WIP_TRANSACTIONS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH ASSET_WO AS (
    SELECT
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        COUNT(DISTINCT EWO.WIP_ENTITY_ID) AS TOTAL_WORK_ORDERS,
        SUM(CASE WHEN EWO.WORK_ORDER_TYPE_DISP = 'DM' THEN 1 ELSE 0 END) AS DM_WORK_ORDERS,
        SUM(CASE WHEN EWO.WIP_ENTITY_NAME LIKE 'PM%' THEN 1 ELSE 0 END) AS PM_WORK_ORDERS
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.ASSET_NUMBER IS NOT NULL
      AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
    GROUP BY EWO.ASSET_NUMBER, EWO.ASSET_DESCRIPTION
),
ASSET_PARTS AS (
    SELECT
        EWO.ASSET_NUMBER,
        COUNT(MMT.TRANSACTION_ID) AS TOTAL_PART_TRANSACTIONS,
        SUM(ABS(MMT.TRANSACTION_QUANTITY)) AS TOTAL_PARTS_CONSUMED,
        SUM(ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST)) AS TOTAL_MATERIAL_COST
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
        ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
       AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
       AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
       AND MMT.TRANSACTION_QUANTITY < 0
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND MMT.TRANSACTION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
    GROUP BY EWO.ASSET_NUMBER
),
ASSET_TIME AS (
    SELECT
        EWO.ASSET_NUMBER,
        COUNT(DISTINCT TO_CHAR(EWO.WIP_ENTITY_ID) || ':' || TO_CHAR(WT.OPERATION_SEQ_NUM)) AS OPERATION_COUNT,
        COUNT(WT.ROWID) AS TIME_TRANSACTION_COUNT,
        SUM(WT.TRANSACTION_QUANTITY) AS TOTAL_TIME_CHARGED_HOURS,
        AVG(WT.TRANSACTION_QUANTITY) AS AVG_TIME_PER_TRANSACTION
    FROM WIP.WIP_TRANSACTIONS WT
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.WIP_ENTITY_ID = WT.WIP_ENTITY_ID
       AND EWO.ORGANIZATION_ID = WT.ORGANIZATION_ID
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    LEFT JOIN BOM.BOM_RESOURCES BR
        ON BR.RESOURCE_ID = WT.RESOURCE_ID
       AND BR.ORGANIZATION_ID = WT.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
      AND BR.UNIT_OF_MEASURE = 'HR'
    GROUP BY EWO.ASSET_NUMBER
)
SELECT *
FROM (
    SELECT
        AW.ASSET_NUMBER,
        AW.ASSET_DESCRIPTION,
        AW.TOTAL_WORK_ORDERS,
        AW.DM_WORK_ORDERS,
        AW.PM_WORK_ORDERS,
        NVL(AP.TOTAL_PART_TRANSACTIONS, 0) AS TOTAL_PART_TRANSACTIONS,
        NVL(AP.TOTAL_PARTS_CONSUMED, 0) AS TOTAL_PARTS_CONSUMED,
        NVL(AP.TOTAL_MATERIAL_COST, 0) AS TOTAL_MATERIAL_COST,
        NVL(AT.OPERATION_COUNT, 0) AS OPERATION_COUNT,
        NVL(AT.TIME_TRANSACTION_COUNT, 0) AS TIME_TRANSACTION_COUNT,
        NVL(AT.TOTAL_TIME_CHARGED_HOURS, 0) AS TOTAL_TIME_CHARGED_HOURS,
        NVL(AT.AVG_TIME_PER_TRANSACTION, 0) AS AVG_TIME_PER_TRANSACTION,
        RANK() OVER (ORDER BY AW.TOTAL_WORK_ORDERS DESC) AS RANK_BY_WO,
        RANK() OVER (ORDER BY NVL(AP.TOTAL_PARTS_CONSUMED, 0) DESC) AS RANK_BY_PARTS,
        RANK() OVER (ORDER BY NVL(AP.TOTAL_MATERIAL_COST, 0) DESC) AS RANK_BY_MATERIAL_COST,
        RANK() OVER (ORDER BY NVL(AT.TOTAL_TIME_CHARGED_HOURS, 0) DESC) AS RANK_BY_TIME_CHARGED
    FROM ASSET_WO AW
    LEFT JOIN ASSET_PARTS AP
        ON AP.ASSET_NUMBER = AW.ASSET_NUMBER
    LEFT JOIN ASSET_TIME AT
        ON AT.ASSET_NUMBER = AW.ASSET_NUMBER
    ORDER BY AW.TOTAL_WORK_ORDERS DESC
)
WHERE ROWNUM <= __LIMIT__;

SPOOL OFF
EXIT
```

### 3. Audit trail full

**File:** `sql/audit_trail_full.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Tracks created/updated activity by user across QA_RESULTS, WIP_ENTITIES, and WIP_OPERATIONS from a supplied start date.
**Parameters:** __DATE_FROM__, __USER_ID__
**Referenced objects:** APPS.QA_RESULTS, APPS.WIP_ENTITIES, APPS.WIP_OPERATIONS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT *
FROM (
    SELECT
        'QA_RESULTS' AS SOURCE_TABLE,
        QR.WORK_ORDER_ID AS ENTITY_ID,
        NVL(QR.QA_LAST_UPDATE_DATE, QR.QA_CREATION_DATE) AS CHANGE_DATE,
        CASE
            WHEN QR.QA_CREATED_BY = __USER_ID__ THEN 'CREATED'
            WHEN QR.QA_LAST_UPDATED_BY = __USER_ID__ THEN 'UPDATED'
        END AS ACTION
    FROM APPS.QA_RESULTS QR
    WHERE __USER_ID__ IN (QR.QA_CREATED_BY, QR.QA_LAST_UPDATED_BY)
      AND NVL(QR.QA_LAST_UPDATE_DATE, QR.QA_CREATION_DATE) >= TO_DATE(__DATE_FROM__, 'YYYY-MM-DD')
    UNION ALL
    SELECT
        'WIP_ENTITIES',
        WE.WIP_ENTITY_ID,
        NVL(WE.LAST_UPDATE_DATE, WE.CREATION_DATE),
        CASE
            WHEN WE.CREATED_BY = __USER_ID__ THEN 'CREATED'
            WHEN WE.LAST_UPDATED_BY = __USER_ID__ THEN 'UPDATED'
        END
    FROM APPS.WIP_ENTITIES WE
    WHERE __USER_ID__ IN (WE.CREATED_BY, WE.LAST_UPDATED_BY)
      AND NVL(WE.LAST_UPDATE_DATE, WE.CREATION_DATE) >= TO_DATE(__DATE_FROM__, 'YYYY-MM-DD')
    UNION ALL
    SELECT
        'WIP_OPERATIONS',
        WO.WIP_ENTITY_ID,
        WO.LAST_UPDATE_DATE,
        'UPDATED'
    FROM APPS.WIP_OPERATIONS WO
    WHERE WO.LAST_UPDATED_BY = __USER_ID__
      AND WO.LAST_UPDATE_DATE >= TO_DATE(__DATE_FROM__, 'YYYY-MM-DD')
)
ORDER BY CHANGE_DATE DESC;

SPOOL OFF
EXIT
```

### 4. Audit trail quick

**File:** `sql/audit_trail_quick.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Quick user update history across QA_RESULTS, WIP_ENTITIES, and WIP_OPERATIONS without a date filter.
**Parameters:** __USER_ID__
**Referenced objects:** APPS.QA_RESULTS, APPS.WIP_ENTITIES, APPS.WIP_OPERATIONS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT *
FROM (
    SELECT
        'QA_RESULTS' AS SOURCE_TABLE,
        QR.WORK_ORDER_ID AS ENTITY_ID,
        QR.QA_LAST_UPDATE_DATE AS CHANGE_DATE
    FROM APPS.QA_RESULTS QR
    WHERE QR.QA_LAST_UPDATED_BY = __USER_ID__
    UNION ALL
    SELECT
        'WIP_ENTITIES',
        WE.WIP_ENTITY_ID,
        WE.LAST_UPDATE_DATE
    FROM APPS.WIP_ENTITIES WE
    WHERE WE.LAST_UPDATED_BY = __USER_ID__
    UNION ALL
    SELECT
        'WIP_OPERATIONS',
        WO.WIP_ENTITY_ID,
        WO.LAST_UPDATE_DATE
    FROM APPS.WIP_OPERATIONS WO
    WHERE WO.LAST_UPDATED_BY = __USER_ID__
)
ORDER BY CHANGE_DATE DESC;

SPOOL OFF
EXIT
```

### 5. Cancelled work orders - last 15 days

**File:** `sql/cancelled_work_orders_15_days.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Exports recent QA rows tied to cancelled work orders for org 1169.
**Parameters:** None
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.QA_RESULTS

```sql
/* ------------------------------------------------------------
   Cancelled Work Orders â€“ Last 15 Days
   Org: 1169
   Status: Cancelled
   Output file passed as &1
------------------------------------------------------------ */

SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET DEFINE ON

-- SQLcl CSV formatting (preferred in SQLcl)
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME,
    EWO.CREATION_DATE,
    QR.QA_CREATION_DATE,
    QR.WORK_ORDER_ID,
    EWO.WORK_ORDER_STATUS,
    QR.MAINTENANCE_OP_SEQ,
    EWO.ASSET_ACTIVITY,
    EWO.ASSET_GROUP_ID,
    EWO.ASSET_DESCRIPTION,
    EWO.CLASS_CODE,
    QR.COLLECTION_ID,
    QR.OCCURRENCE,
    QR.PLAN_ID,
    QR.STATUS,
    QR.CHARACTER1 AS "Lot Number",
    QR.CHARACTER2 AS "Location",
    QR.CHARACTER3 AS "Reason",
    QR.CHARACTER4 AS "Adjustment",
    QR.COMMENT1   AS "Description"
FROM APPS.QA_RESULTS QR
JOIN APPS.EAM_WORK_ORDERS_V EWO
  ON QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
 AND QR.WORK_ORDER_ID  = EWO.WIP_ENTITY_ID
WHERE
    QR.QA_CREATION_DATE > SYSDATE - 15
AND QR.ORGANIZATION_ID = 1169
AND EWO.WORK_ORDER_STATUS = 'Cancelled'
ORDER BY
    QR.QA_CREATION_DATE DESC,
    QR.QA_LAST_UPDATE_DATE DESC;

SPOOL OFF
EXIT
```

### 6. Configured BOM for asset

**File:** `sql/configured_bom_for_asset.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Returns the configured Oracle BOM for one asset using the latest asset context and common bill sequence.
**Parameters:** __ACTIVE_ONLY__, __ASSET_NUMBER__, __ORG_CODE__
**Referenced objects:** APPS.BOM_BILL_OF_MATERIALS, APPS.BOM_INVENTORY_COMPONENTS, APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, INV.MTL_SYSTEM_ITEMS_B

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH ASSET_CONTEXT AS (
    SELECT *
    FROM (
        SELECT
            EWO.ORGANIZATION_ID,
            EWO.ASSET_NUMBER,
            EWO.ASSET_DESCRIPTION,
            EWO.ASSET_GROUP_ID,
            EWO.WIP_ENTITY_NAME AS LATEST_WORK_ORDER,
            EWO.CREATION_DATE AS LATEST_WO_CREATION_DATE,
            ROW_NUMBER() OVER (
                PARTITION BY EWO.ORGANIZATION_ID, EWO.ASSET_NUMBER, EWO.ASSET_GROUP_ID
                ORDER BY EWO.CREATION_DATE DESC, EWO.WIP_ENTITY_ID DESC
            ) AS RN
        FROM APPS.EAM_WORK_ORDERS_V EWO
        JOIN APPS.MTL_PARAMETERS MP
            ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
        WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
          AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
          AND EWO.ASSET_GROUP_ID IS NOT NULL
    )
    WHERE RN = 1
)
SELECT
    AC.ASSET_NUMBER,
    AC.ASSET_DESCRIPTION,
    AG.SEGMENT1 AS ASSET_GROUP_ITEM,
    AG.DESCRIPTION AS ASSET_GROUP_DESCRIPTION,
    BBOM.BILL_SEQUENCE_ID,
    BBOM.COMMON_BILL_SEQUENCE_ID,
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BBOM.ASSEMBLY_TYPE,
    BIC.ITEM_NUM,
    BIC.COMPONENT_SEQUENCE_ID,
    COMP.SEGMENT1 AS PART_NUMBER,
    COMP.DESCRIPTION AS PART_DESCRIPTION,
    BIC.COMPONENT_QUANTITY,
    COMP.PRIMARY_UOM_CODE AS COMPONENT_UOM,
    BIC.COMPONENT_YIELD_FACTOR,
    BIC.COMPONENT_REMARKS,
    TO_CHAR(BIC.EFFECTIVITY_DATE, 'MM/DD/YYYY') AS EFFECTIVITY_DATE,
    TO_CHAR(BIC.DISABLE_DATE, 'MM/DD/YYYY') AS DISABLE_DATE,
    CASE
        WHEN BIC.EFFECTIVITY_DATE <= SYSDATE
         AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
        THEN 'Y'
        ELSE 'N'
    END AS CURRENTLY_ACTIVE,
    AC.LATEST_WORK_ORDER,
    TO_CHAR(AC.LATEST_WO_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS LATEST_WO_CREATION_DATE
FROM ASSET_CONTEXT AC
JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
    ON BBOM.ASSEMBLY_ITEM_ID = AC.ASSET_GROUP_ID
   AND BBOM.ORGANIZATION_ID = AC.ORGANIZATION_ID
JOIN APPS.BOM_INVENTORY_COMPONENTS BIC
    ON BIC.BILL_SEQUENCE_ID = BBOM.COMMON_BILL_SEQUENCE_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B AG
    ON AG.INVENTORY_ITEM_ID = AC.ASSET_GROUP_ID
   AND AG.ORGANIZATION_ID = AC.ORGANIZATION_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B COMP
    ON COMP.INVENTORY_ITEM_ID = BIC.COMPONENT_ITEM_ID
   AND COMP.ORGANIZATION_ID = AC.ORGANIZATION_ID
WHERE __ACTIVE_ONLY__ = 0
   OR (
        BIC.EFFECTIVITY_DATE <= SYSDATE
        AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
      )
ORDER BY
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BIC.ITEM_NUM,
    COMP.SEGMENT1;

SPOOL OFF
EXIT
```

### 7. Configured BOMs for class code

**File:** `sql/configured_boms_for_class_code.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Returns configured BOM rows for assets in a class code, including latest work-order context.
**Parameters:** __ACTIVE_ONLY__, __CLASS_CODE__, __ORG_CODE__
**Referenced objects:** APPS.BOM_BILL_OF_MATERIALS, APPS.BOM_INVENTORY_COMPONENTS, APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, INV.MTL_SYSTEM_ITEMS_B

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH CLASS_ASSETS AS (
    SELECT
        EWO.ORGANIZATION_ID,
        EWO.CLASS_CODE,
        EWO.ASSET_NUMBER,
        MAX(EWO.ASSET_DESCRIPTION) AS ASSET_DESCRIPTION,
        EWO.ASSET_GROUP_ID,
        MAX(EWO.CREATION_DATE) AS LATEST_WO_CREATION_DATE
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.CLASS_CODE = __CLASS_CODE__
      AND EWO.ASSET_NUMBER IS NOT NULL
      AND EWO.ASSET_GROUP_ID IS NOT NULL
    GROUP BY
        EWO.ORGANIZATION_ID,
        EWO.CLASS_CODE,
        EWO.ASSET_NUMBER,
        EWO.ASSET_GROUP_ID
),
LATEST_WO AS (
    SELECT
        CA.ORGANIZATION_ID,
        CA.ASSET_NUMBER,
        CA.ASSET_GROUP_ID,
        MAX(EWO.WIP_ENTITY_NAME) KEEP (
            DENSE_RANK LAST ORDER BY EWO.CREATION_DATE, EWO.WIP_ENTITY_ID
        ) AS LATEST_WORK_ORDER
    FROM CLASS_ASSETS CA
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.ORGANIZATION_ID = CA.ORGANIZATION_ID
       AND EWO.CLASS_CODE = CA.CLASS_CODE
       AND EWO.ASSET_NUMBER = CA.ASSET_NUMBER
       AND EWO.ASSET_GROUP_ID = CA.ASSET_GROUP_ID
       AND EWO.CREATION_DATE = CA.LATEST_WO_CREATION_DATE
    GROUP BY
        CA.ORGANIZATION_ID,
        CA.ASSET_NUMBER,
        CA.ASSET_GROUP_ID
)
SELECT
    CA.CLASS_CODE,
    CA.ASSET_NUMBER,
    CA.ASSET_DESCRIPTION,
    AG.SEGMENT1 AS ASSET_GROUP_ITEM,
    AG.DESCRIPTION AS ASSET_GROUP_DESCRIPTION,
    BBOM.BILL_SEQUENCE_ID,
    BBOM.COMMON_BILL_SEQUENCE_ID,
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BBOM.ASSEMBLY_TYPE,
    BIC.ITEM_NUM,
    BIC.COMPONENT_SEQUENCE_ID,
    COMP.SEGMENT1 AS PART_NUMBER,
    COMP.DESCRIPTION AS PART_DESCRIPTION,
    BIC.COMPONENT_QUANTITY,
    COMP.PRIMARY_UOM_CODE AS COMPONENT_UOM,
    BIC.COMPONENT_YIELD_FACTOR,
    BIC.COMPONENT_REMARKS,
    TO_CHAR(BIC.EFFECTIVITY_DATE, 'MM/DD/YYYY') AS EFFECTIVITY_DATE,
    TO_CHAR(BIC.DISABLE_DATE, 'MM/DD/YYYY') AS DISABLE_DATE,
    CASE
        WHEN BIC.EFFECTIVITY_DATE <= SYSDATE
         AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
        THEN 'Y'
        ELSE 'N'
    END AS CURRENTLY_ACTIVE,
    LWO.LATEST_WORK_ORDER,
    TO_CHAR(CA.LATEST_WO_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS LATEST_WO_CREATION_DATE
FROM CLASS_ASSETS CA
LEFT JOIN LATEST_WO LWO
    ON LWO.ORGANIZATION_ID = CA.ORGANIZATION_ID
   AND LWO.ASSET_NUMBER = CA.ASSET_NUMBER
   AND LWO.ASSET_GROUP_ID = CA.ASSET_GROUP_ID
JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
    ON BBOM.ASSEMBLY_ITEM_ID = CA.ASSET_GROUP_ID
   AND BBOM.ORGANIZATION_ID = CA.ORGANIZATION_ID
JOIN APPS.BOM_INVENTORY_COMPONENTS BIC
    ON BIC.BILL_SEQUENCE_ID = BBOM.COMMON_BILL_SEQUENCE_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B AG
    ON AG.INVENTORY_ITEM_ID = CA.ASSET_GROUP_ID
   AND AG.ORGANIZATION_ID = CA.ORGANIZATION_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B COMP
    ON COMP.INVENTORY_ITEM_ID = BIC.COMPONENT_ITEM_ID
   AND COMP.ORGANIZATION_ID = CA.ORGANIZATION_ID
WHERE __ACTIVE_ONLY__ = 0
   OR (
        BIC.EFFECTIVITY_DATE <= SYSDATE
        AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
      )
ORDER BY
    CA.CLASS_CODE,
    CA.ASSET_NUMBER,
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BIC.ITEM_NUM,
    COMP.SEGMENT1;

SPOOL OFF
EXIT
```

### 8. Configured BOMs for department

**File:** `sql/configured_boms_for_department.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Returns configured BOM rows for released PM assets assigned to a department and optional operation sequence.
**Parameters:** __ACTIVE_ONLY__, __DEPARTMENT_CODE__, __OPERATION_SEQ__, __ORG_CODE__
**Referenced objects:** APPS.BOM_BILL_OF_MATERIALS, APPS.BOM_INVENTORY_COMPONENTS, APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, APPS.WIP_OPERATIONS_V, INV.MTL_SYSTEM_ITEMS_B

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH DEPT_ASSETS AS (
    SELECT DISTINCT
        EWO.ORGANIZATION_ID,
        WO.DEPARTMENT_CODE,
        WO.OPERATION_SEQ_NUM AS MATCHED_OPERATION_SEQ,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        EWO.ASSET_GROUP_ID
    FROM APPS.WIP_OPERATIONS_V WO
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.WIP_ENTITY_ID = WO.WIP_ENTITY_ID
       AND EWO.ORGANIZATION_ID = WO.ORGANIZATION_ID
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND WO.DEPARTMENT_CODE = __DEPARTMENT_CODE__
      AND (__OPERATION_SEQ__ = 0 OR WO.OPERATION_SEQ_NUM = __OPERATION_SEQ__)
      AND EWO.WIP_ENTITY_NAME LIKE 'PM%'
      AND EWO.WORK_ORDER_STATUS = 'Released'
      AND EWO.ASSET_NUMBER IS NOT NULL
      AND EWO.ASSET_GROUP_ID IS NOT NULL
)
SELECT
    DA.DEPARTMENT_CODE,
    DA.MATCHED_OPERATION_SEQ,
    DA.ASSET_NUMBER,
    DA.ASSET_DESCRIPTION,
    AG.SEGMENT1 AS ASSET_GROUP_ITEM,
    AG.DESCRIPTION AS ASSET_GROUP_DESCRIPTION,
    BBOM.BILL_SEQUENCE_ID,
    BBOM.COMMON_BILL_SEQUENCE_ID,
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BBOM.ASSEMBLY_TYPE,
    BIC.ITEM_NUM,
    BIC.COMPONENT_SEQUENCE_ID,
    COMP.SEGMENT1 AS PART_NUMBER,
    COMP.DESCRIPTION AS PART_DESCRIPTION,
    BIC.COMPONENT_QUANTITY,
    COMP.PRIMARY_UOM_CODE AS COMPONENT_UOM,
    BIC.COMPONENT_YIELD_FACTOR,
    BIC.COMPONENT_REMARKS,
    TO_CHAR(BIC.EFFECTIVITY_DATE, 'MM/DD/YYYY') AS EFFECTIVITY_DATE,
    TO_CHAR(BIC.DISABLE_DATE, 'MM/DD/YYYY') AS DISABLE_DATE,
    CASE
        WHEN BIC.EFFECTIVITY_DATE <= SYSDATE
         AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
        THEN 'Y'
        ELSE 'N'
    END AS CURRENTLY_ACTIVE
FROM DEPT_ASSETS DA
JOIN APPS.BOM_BILL_OF_MATERIALS BBOM
    ON BBOM.ASSEMBLY_ITEM_ID = DA.ASSET_GROUP_ID
   AND BBOM.ORGANIZATION_ID = DA.ORGANIZATION_ID
JOIN APPS.BOM_INVENTORY_COMPONENTS BIC
    ON BIC.BILL_SEQUENCE_ID = BBOM.COMMON_BILL_SEQUENCE_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B AG
    ON AG.INVENTORY_ITEM_ID = DA.ASSET_GROUP_ID
   AND AG.ORGANIZATION_ID = DA.ORGANIZATION_ID
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B COMP
    ON COMP.INVENTORY_ITEM_ID = BIC.COMPONENT_ITEM_ID
   AND COMP.ORGANIZATION_ID = DA.ORGANIZATION_ID
WHERE __ACTIVE_ONLY__ = 0
   OR (
        BIC.EFFECTIVITY_DATE <= SYSDATE
        AND (BIC.DISABLE_DATE IS NULL OR BIC.DISABLE_DATE > SYSDATE)
      )
ORDER BY
    DA.DEPARTMENT_CODE,
    DA.ASSET_NUMBER,
    BBOM.ALTERNATE_BOM_DESIGNATOR,
    BIC.ITEM_NUM,
    COMP.SEGMENT1;

SPOOL OFF
EXIT
```

### 9. Employees for resource

**File:** `sql/employees_for_resource.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Reverse lookup from a resource code to active employees assigned to that resource.
**Parameters:** __ORG_CODE__, __RESOURCE_CODE__
**Referenced objects:** APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, BOM.BOM_RESOURCE_EMPLOYEES, BOM.BOM_RESOURCES

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    BR.RESOURCE_CODE,
    BR.DESCRIPTION AS RESOURCE_DESCRIPTION,
    BR.RESOURCE_TYPE,
    PEO.FULL_NAME,
    FU.USER_NAME AS BADGE_NUMBER,
    FU.EMAIL_ADDRESS,
    BRE.EFFECTIVE_START_DATE,
    BRE.EFFECTIVE_END_DATE
FROM BOM.BOM_RESOURCES BR
JOIN BOM.BOM_RESOURCE_EMPLOYEES BRE
    ON BRE.RESOURCE_ID = BR.RESOURCE_ID
   AND BRE.ORGANIZATION_ID = BR.ORGANIZATION_ID
JOIN APPS.PER_ALL_PEOPLE_F PEO
    ON PEO.PERSON_ID = BRE.PERSON_ID
   AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
LEFT JOIN APPS.FND_USER FU
    ON FU.EMPLOYEE_ID = PEO.PERSON_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = BR.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND BR.RESOURCE_CODE = __RESOURCE_CODE__
  AND SYSDATE <= BRE.EFFECTIVE_END_DATE
ORDER BY PEO.FULL_NAME;

SPOOL OFF
EXIT
```

### 10. Open DM work orders at operation 10

**File:** `sql/level10_dm_open.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists open DM work orders at operation sequence 10 with assigned resource instance context.
**Parameters:** None
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, APPS.WIP_OP_RESOURCE_INSTANCES_V, APPS.WIP_OPERATIONS_V

```sql
-- level10_dm_open.sql
-- Level 10 DM Open Work Orders
-- Output file passed as &1

WHENEVER SQLERROR EXIT SQL.SQLCODE
WHENEVER OSERROR EXIT 1

SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET DEFINE ON
SET SQLFORMAT CSV

SPOOL &1

SELECT DISTINCT
    EWO.WIP_ENTITY_NAME,
    EWO.WIP_ENTITY_ID,
    TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS CREATION_DATE_TIME,
    EWO.ASSET_NUMBER,
    EWO.WORK_ORDER_STATUS,
    WO2.OPERATION_SEQ_NUM,
    WO2.OPERATION_COMPLETED,
    RES.INSTANCE_NAME,
    EWO.DESCRIPTION
FROM
    APPS.WIP_OPERATIONS_V WO1
JOIN APPS.EAM_WORK_ORDERS_V EWO
    ON EWO.WIP_ENTITY_ID = WO1.WIP_ENTITY_ID
JOIN APPS.WIP_OPERATIONS_V WO2
    ON EWO.WIP_ENTITY_ID = WO2.WIP_ENTITY_ID
JOIN APPS.WIP_OP_RESOURCE_INSTANCES_V RES
    ON RES.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
   AND RES.OPERATION_SEQ_NUM = WO2.OPERATION_SEQ_NUM
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE
    EWO.ORGANIZATION_ID = 1169
    AND WO1.OPERATION_SEQ_NUM = 10
    AND WO2.OPERATION_SEQ_NUM = 10
    AND WO1.OPERATION_COMPLETED = 'N'
    AND EWO.USER_DEFINED_STATUS_ID = 3
    AND MP.ORGANIZATION_CODE = 'XAU'
    AND EWO.WORK_ORDER_TYPE_DISP = 'DM'
    AND EWO.ASSET_NUMBER LIKE 'AU%'
ORDER BY
    CREATION_DATE_TIME ASC;

SPOOL OFF
EXIT
```

### 11. Lookup user

**File:** `sql/lookup_user.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Finds an Oracle user by user name, user ID, or Oracle person ID (`FND_USER.EMPLOYEE_ID`). Visible HR employee numbers live in `PER_ALL_PEOPLE_F.EMPLOYEE_NUMBER`.
**Parameters:** __IDENTIFIER__
**Referenced objects:** APPS.FND_USER

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    USER_ID,
    USER_NAME,
    DESCRIPTION AS FULL_NAME,
    EMAIL_ADDRESS,
    EMPLOYEE_ID,
    END_DATE
FROM APPS.FND_USER
WHERE USER_NAME = __IDENTIFIER__
   OR TO_CHAR(USER_ID) = __IDENTIFIER__
   OR TO_CHAR(EMPLOYEE_ID) = __IDENTIFIER__;

SPOOL OFF
EXIT
```

### 12. Parts charged to work order

**File:** `sql/parts_charged_to_work_order.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists inventory material transactions charged to a work order, including unit and line material cost.
**Parameters:** __ORG_CODE__, __WORK_ORDER__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, INV.MTL_MATERIAL_TRANSACTIONS, INV.MTL_SYSTEM_ITEMS_B, INV.MTL_TRANSACTION_TYPES

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    MTT.TRANSACTION_TYPE_NAME AS TRANSACTION_TYPE,
    TO_CHAR(MMT.TRANSACTION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS TRANSACTION_DATE,
    MSI.SEGMENT1 AS PART_NUMBER,
    MSI.DESCRIPTION AS PART_DESCRIPTION,
    MMT.TRANSACTION_QUANTITY AS QTY,
    NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS UNIT_MATERIAL_COST,
    ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS LINE_MATERIAL_COST,
    MMT.TRANSACTION_UOM AS UOM,
    MMT.SUBINVENTORY_CODE AS FROM_SUBINVENTORY,
    MMT.TRANSACTION_REFERENCE AS REFERENCE
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
    ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
   AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
JOIN INV.MTL_SYSTEM_ITEMS_B MSI
    ON MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
   AND MSI.ORGANIZATION_ID = MMT.ORGANIZATION_ID
JOIN INV.MTL_TRANSACTION_TYPES MTT
    ON MTT.TRANSACTION_TYPE_ID = MMT.TRANSACTION_TYPE_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.WIP_ENTITY_NAME = __WORK_ORDER__
ORDER BY MMT.TRANSACTION_DATE DESC;

SPOOL OFF
EXIT
```

### 13. Parts consumption by asset

**File:** `sql/parts_consumption_by_asset.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Summarizes parts issued to work orders for one asset over a rolling month window.
**Parameters:** __ASSET_NUMBER__, __MONTHS__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, INV.MTL_MATERIAL_TRANSACTIONS, INV.MTL_SYSTEM_ITEMS_B

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    MSI.SEGMENT1 AS PART_NUMBER,
    MSI.DESCRIPTION AS PART_DESCRIPTION,
    COUNT(MMT.TRANSACTION_ID) AS TIMES_ISSUED,
    SUM(ABS(MMT.TRANSACTION_QUANTITY)) AS TOTAL_QTY_CONSUMED,
    SUM(ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST)) AS TOTAL_MATERIAL_COST,
    MMT.TRANSACTION_UOM AS UOM
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
    ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
   AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
   AND MMT.TRANSACTION_QUANTITY < 0
JOIN INV.MTL_SYSTEM_ITEMS_B MSI
    ON MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
   AND MSI.ORGANIZATION_ID = MMT.ORGANIZATION_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
  AND MMT.TRANSACTION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
GROUP BY EWO.ASSET_NUMBER, EWO.ASSET_DESCRIPTION, MSI.SEGMENT1, MSI.DESCRIPTION, MMT.TRANSACTION_UOM
ORDER BY TOTAL_MATERIAL_COST DESC, TOTAL_QTY_CONSUMED DESC;

SPOOL OFF
EXIT
```

### 14. Person parts history

**File:** `sql/person_parts_history.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Uses QA activity to find work orders touched by a person, then lists issued parts for those work orders.
**Parameters:** __DAYS__, __NAME__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS, INV.MTL_MATERIAL_TRANSACTIONS, INV.MTL_SYSTEM_ITEMS_B, INV.MTL_TRANSACTION_TYPES

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH PERSON_MATCH AS (
    SELECT
        FU.USER_ID,
        FU.USER_NAME AS BADGE_NUMBER,
        PEO.FULL_NAME
    FROM APPS.PER_ALL_PEOPLE_F PEO
    JOIN APPS.FND_USER FU
        ON FU.EMPLOYEE_ID = PEO.PERSON_ID
    WHERE SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
      AND (
            UPPER(PEO.FULL_NAME) LIKE UPPER('%' || __NAME__ || '%')
         OR UPPER(FU.DESCRIPTION) LIKE UPPER('%' || __NAME__ || '%')
         OR UPPER(FU.USER_NAME) LIKE UPPER('%' || __NAME__ || '%')
      )
),
TOUCHED_WO AS (
    SELECT DISTINCT
        PM.FULL_NAME,
        PM.BADGE_NUMBER,
        EWO.ORGANIZATION_ID,
        EWO.WIP_ENTITY_ID,
        EWO.WIP_ENTITY_NAME AS WORK_ORDER,
        EWO.WORK_ORDER_STATUS,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        MAX(QR.QA_CREATION_DATE) OVER (
            PARTITION BY EWO.ORGANIZATION_ID, EWO.WIP_ENTITY_ID
        ) AS LAST_TOUCH_DATE
    FROM PERSON_MATCH PM
    JOIN APPS.QA_RESULTS QR
        ON QR.QA_CREATED_BY = PM.USER_ID
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.WIP_ENTITY_ID = QR.WORK_ORDER_ID
       AND EWO.ORGANIZATION_ID = QR.ORGANIZATION_ID
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = QR.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND QR.QA_CREATION_DATE >= SYSDATE - __DAYS__
)
SELECT
    TWO.FULL_NAME,
    TWO.BADGE_NUMBER,
    TWO.WORK_ORDER,
    TWO.WORK_ORDER_STATUS,
    TWO.ASSET_NUMBER,
    TWO.ASSET_DESCRIPTION,
    TO_CHAR(TWO.LAST_TOUCH_DATE, 'MM/DD/YYYY HH24:MI:SS') AS LAST_TOUCH_DATE,
    MTT.TRANSACTION_TYPE_NAME AS TRANSACTION_TYPE,
    TO_CHAR(MMT.TRANSACTION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS TRANSACTION_DATE,
    MSI.SEGMENT1 AS PART_NUMBER,
    MSI.DESCRIPTION AS PART_DESCRIPTION,
    MMT.TRANSACTION_QUANTITY AS QTY,
    NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS UNIT_MATERIAL_COST,
    ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS LINE_MATERIAL_COST,
    MMT.TRANSACTION_UOM AS UOM,
    MMT.SUBINVENTORY_CODE AS FROM_SUBINVENTORY,
    MMT.TRANSACTION_REFERENCE AS REFERENCE
FROM TOUCHED_WO TWO
JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
    ON MMT.TRANSACTION_SOURCE_ID = TWO.WIP_ENTITY_ID
   AND MMT.ORGANIZATION_ID = TWO.ORGANIZATION_ID
   AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
   AND MMT.TRANSACTION_QUANTITY < 0
JOIN INV.MTL_SYSTEM_ITEMS_B MSI
    ON MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
   AND MSI.ORGANIZATION_ID = MMT.ORGANIZATION_ID
LEFT JOIN INV.MTL_TRANSACTION_TYPES MTT
    ON MTT.TRANSACTION_TYPE_ID = MMT.TRANSACTION_TYPE_ID
ORDER BY
    TWO.LAST_TOUCH_DATE DESC,
    TWO.WORK_ORDER,
    MMT.TRANSACTION_DATE DESC,
    MSI.SEGMENT1;

SPOOL OFF
EXIT
```

### 15. Person work-order history

**File:** `sql/person_work_order_history.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists work orders completed or touched by a named employee using QA submissions over a rolling window.
**Parameters:** __DAYS__, __NAME__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT DISTINCT
    PEO.FULL_NAME,
    FU.USER_NAME AS BADGE_NUMBER,
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.ASSET_NUMBER,
    EWO.ASSET_ACTIVITY,
    EWO.ASSET_DESCRIPTION,
    TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
    QR.CHARACTER1 AS LOT_NUMBER,
    QR.CHARACTER2 AS LOCATION,
    QR.CHARACTER3 AS REASON,
    QR.CHARACTER4 AS ADJUSTMENT,
    QR.COMMENT1 AS DESCRIPTION
FROM APPS.PER_ALL_PEOPLE_F PEO
JOIN APPS.FND_USER FU
    ON FU.EMPLOYEE_ID = PEO.PERSON_ID
JOIN APPS.QA_RESULTS QR
    ON QR.QA_CREATED_BY = FU.USER_ID
JOIN APPS.EAM_WORK_ORDERS_V EWO
    ON EWO.WIP_ENTITY_ID = QR.WORK_ORDER_ID
   AND EWO.ORGANIZATION_ID = QR.ORGANIZATION_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = QR.ORGANIZATION_ID
WHERE SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
  AND MP.ORGANIZATION_CODE = __ORG_CODE__
  AND UPPER(PEO.FULL_NAME) LIKE UPPER('%' || __NAME__ || '%')
  AND QR.QA_CREATION_DATE >= SYSDATE - __DAYS__
ORDER BY QR.QA_CREATION_DATE DESC;

SPOOL OFF
EXIT
```

### 16. Released PM work orders

**File:** `sql/pm_released_work_orders.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Exports currently released PM work orders for org 1169 with asset and schedule context.
**Parameters:** None
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, APPS.WIP_OPERATIONS_V, EAM.EAM_PM_SCHEDULING_RULES

```sql
-- pm_released_work_orders.sql
-- Released PM work orders
-- Output file passed as &1 from SQLcl

SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET DEFINE ON

-- SQLcl CSV formatting (preferred in SQLcl)
SET SQLFORMAT CSV

SPOOL &1

SELECT DISTINCT
    EWO.WIP_ENTITY_NAME,
    TO_CHAR(EWO.CREATION_DATE,'MM/DD/YYYY HH24:MI:SS') AS CREATION_DATE_TIME,
    EWO.ASSET_NUMBER,
    EWO.ASSET_ACTIVITY,
    WO2.DEPARTMENT_CODE,
    EWO.WIP_ENTITY_ID,
    EWO.ASSET_DESCRIPTION,
    EWO.WORK_ORDER_STATUS,
    WO2.OPERATION_SEQ_NUM,
    WO2.OPERATION_COMPLETED,
    SCHEDULED_START_DATE
FROM
    EAM.EAM_PM_SCHEDULING_RULES,
    APPS.WIP_OPERATIONS_V WO1,
    APPS.EAM_WORK_ORDERS_V EWO,
    APPS.MTL_PARAMETERS MP,
    APPS.WIP_OPERATIONS_V WO2
WHERE
    EWO.WIP_ENTITY_ID = WO1.WIP_ENTITY_ID
    AND EWO.WIP_ENTITY_ID = WO2.WIP_ENTITY_ID
    AND EWO.ORGANIZATION_ID = 1169
    AND EWO.ORGANIZATION_ID = MP.ORGANIZATION_ID
    AND WO1.ORGANIZATION_ID = MP.ORGANIZATION_ID
    AND WO1.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    AND WO2.ORGANIZATION_ID = MP.ORGANIZATION_ID
    AND WO2.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    AND WO1.ORGANIZATION_ID = WO2.ORGANIZATION_ID
    AND WO1.WIP_ENTITY_ID = WO2.WIP_ENTITY_ID
    AND MP.ORGANIZATION_CODE = 'XAU'
    AND EWO.WIP_ENTITY_NAME LIKE 'PM%'
    AND EWO.WORK_ORDER_STATUS = 'Released'
    AND EWO.ASSET_NUMBER LIKE 'AU%'
ORDER BY
    CREATION_DATE_TIME ASC;

SPOOL OFF
EXIT
```

### 17. QA daily results - last 24 hours

**File:** `sql/qa_daily_results_24_hours.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Exports QA results from the last 24 hours with work-order and QA group context.
**Parameters:** None
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS

```sql
-- qa_daily_results_24_hours.sql
-- SQLcl-friendly CSV output

SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET DEFINE ON

-- SQLcl CSV formatting (preferred in SQLcl)
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME,
    EWO.CREATION_DATE,
    QR.QA_CREATION_DATE,
    EWO.ASSET_ACTIVITY,
    QR.MAINTENANCE_OP_SEQ,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    (
        SELECT DISTINCT PEO.FULL_NAME
        FROM APPS.FND_USER FU
        JOIN APPS.PER_ALL_PEOPLE_F PEO
            ON PEO.PERSON_ID = FU.EMPLOYEE_ID
        WHERE FU.USER_ID = QR.QA_CREATED_BY
          AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE
                          AND PEO.EFFECTIVE_END_DATE
    ) AS QA_USER_CREATED_BY,
    (
        SELECT DISTINCT PEO.FULL_NAME
        FROM APPS.FND_USER FU
        JOIN APPS.PER_ALL_PEOPLE_F PEO
            ON PEO.PERSON_ID = FU.EMPLOYEE_ID
        WHERE FU.USER_ID = QR.QA_LAST_UPDATED_BY
          AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE
                          AND PEO.EFFECTIVE_END_DATE
    ) AS QA_USER_LAST_UPDATED,
    QR.CHARACTER1 AS "Lot Number",
    QR.CHARACTER2 AS "Location",
    QR.CHARACTER3 AS "Reason",
    QR.CHARACTER4 AS "Adjustment",
    QR.COMMENT1   AS "Description",
    EWO.DESCRIPTION
FROM APPS.QA_RESULTS QR
JOIN APPS.EAM_WORK_ORDERS_V EWO
    ON QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND QR.WORK_ORDER_ID  = EWO.WIP_ENTITY_ID
WHERE
    QR.QA_CREATION_DATE > SYSDATE - 1
    AND QR.ORGANIZATION_ID = 1169
    AND EWO.WIP_ENTITY_NAME LIKE 'AU%'
    AND QR.MAINTENANCE_OP_SEQ = 10
ORDER BY
    QR.QA_CREATION_DATE DESC,
    QR.QA_LAST_UPDATE_DATE DESC;

SPOOL OFF
EXIT
```

### 18. QA group members

**File:** `sql/qa_group_members.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Lists active members of a supplied QA group.
**Parameters:** __GROUP_NAME__
**Referenced objects:** APPS.QA_USER_GROUP_V

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    USER_NAME,
    PERSON_NAME,
    EMAIL_ADDRESS,
    GROUP_NAME,
    STATUS,
    LAST_UPDATE_DATE
FROM APPS.QA_USER_GROUP_V
WHERE GROUP_NAME = __GROUP_NAME__
  AND STATUS = 'A'
ORDER BY PERSON_NAME;

SPOOL OFF
EXIT
```

### 19. QA groups for user

**File:** `sql/qa_groups_for_user.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Lists active QA groups for a supplied user.
**Parameters:** __IDENTIFIER__
**Referenced objects:** APPS.QA_USER_GROUP_V

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    USER_ID,
    USER_NAME,
    PERSON_NAME,
    EMAIL_ADDRESS,
    GROUP_NAME,
    STATUS,
    LAST_UPDATE_DATE
FROM APPS.QA_USER_GROUP_V
WHERE USER_NAME = __IDENTIFIER__
   OR TO_CHAR(USER_ID) = __IDENTIFIER__
ORDER BY GROUP_NAME;

SPOOL OFF
EXIT
```

### 20. QA results for work order

**File:** `sql/qa_results_for_work_order.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists QA results for one work order with technician name and badge number.
**Parameters:** __ORG_CODE__, __WORK_ORDER__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    PEO.FULL_NAME AS TECHNICIAN,
    FU.USER_NAME AS BADGE_NUMBER,
    TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
    QR.MAINTENANCE_OP_SEQ AS OP_SEQ,
    QR.CHARACTER1 AS LOT_NUMBER,
    QR.CHARACTER2 AS LOCATION,
    QR.CHARACTER3 AS REASON,
    QR.CHARACTER4 AS ADJUSTMENT,
    QR.COMMENT1 AS DESCRIPTION
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN APPS.QA_RESULTS QR
    ON QR.WORK_ORDER_ID = EWO.WIP_ENTITY_ID
   AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
JOIN APPS.FND_USER FU
    ON FU.USER_ID = QR.QA_CREATED_BY
JOIN APPS.PER_ALL_PEOPLE_F PEO
    ON PEO.PERSON_ID = FU.EMPLOYEE_ID
   AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.WIP_ENTITY_NAME = __WORK_ORDER__
ORDER BY QR.QA_CREATION_DATE DESC;

SPOOL OFF
EXIT
```

### 21. QA results last 12 hours

**File:** `sql/qa_results_last_12_hours.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Exports last 12 hours of AU operation 10 QA results with creator and updater names.
**Parameters:** None
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS

```sql
-- qa_daily_results_24_hours.sql
-- SQLcl-friendly CSV output


SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET DEFINE ON

-- SQLcl CSV formatting (preferred in SQLcl)
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME,
    EWO.CREATION_DATE,
    QR.QA_CREATION_DATE,
    EWO.ASSET_ACTIVITY,
    QR.MAINTENANCE_OP_SEQ,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    (
        SELECT DISTINCT PEO.FULL_NAME
        FROM APPS.FND_USER FU
        JOIN APPS.PER_ALL_PEOPLE_F PEO
            ON PEO.PERSON_ID = FU.EMPLOYEE_ID
        WHERE FU.USER_ID = QR.QA_CREATED_BY
          AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE
                          AND PEO.EFFECTIVE_END_DATE
    ) AS QA_USER_CREATED_BY,
    (
        SELECT DISTINCT PEO.FULL_NAME
        FROM APPS.FND_USER FU
        JOIN APPS.PER_ALL_PEOPLE_F PEO
            ON PEO.PERSON_ID = FU.EMPLOYEE_ID
        WHERE FU.USER_ID = QR.QA_LAST_UPDATED_BY
          AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE
                          AND PEO.EFFECTIVE_END_DATE
    ) AS QA_USER_LAST_UPDATED,
    QR.CHARACTER1 AS "Lot Number",
    QR.CHARACTER2 AS "Location",
    QR.CHARACTER3 AS "Reason",
    QR.CHARACTER4 AS "Adjustment",
    QR.COMMENT1   AS "Description",
    EWO.DESCRIPTION
FROM APPS.QA_RESULTS QR
JOIN APPS.EAM_WORK_ORDERS_V EWO
    ON QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND QR.WORK_ORDER_ID  = EWO.WIP_ENTITY_ID
WHERE
    QR.QA_CREATION_DATE >= SYSDATE - INTERVAL '12' HOUR
    AND QR.ORGANIZATION_ID = 1169
    AND EWO.WIP_ENTITY_NAME LIKE 'AU%'
    AND QR.MAINTENANCE_OP_SEQ = 10
ORDER BY
    QR.QA_CREATION_DATE DESC,
    QR.QA_LAST_UPDATE_DATE DESC;

SPOOL OFF
EXIT
```

### 22. QA results last 31 days

**File:** `sql/qa_results_last_31_days.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Exports last 31 days of AU operation 10 QA results for monthly reporting.
**Parameters:** None
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.QA_RESULTS

```sql
-- qa_results_last_31_days.sql
-- Parameter: &1 = output CSV file path

SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET DEFINE ON


-- SQLcl CSV formatting (preferred in SQLcl)
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME,
    EWO.CREATION_DATE,
    QR.QA_CREATION_DATE,
    EWO.ASSET_ACTIVITY,
    QR.MAINTENANCE_OP_SEQ,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    QR.CHARACTER1 AS LOT_NUMBER,
    QR.CHARACTER2 AS LOCATION,
    QR.CHARACTER3 AS REASON,
    QR.CHARACTER4 AS ADJUSTMENT,
    QR.COMMENT1   AS DESCRIPTION,
    EWO.DESCRIPTION AS WORK_ORDER_DESCRIPTION
FROM APPS.QA_RESULTS QR
JOIN APPS.EAM_WORK_ORDERS_V EWO
  ON QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
 AND QR.WORK_ORDER_ID  = EWO.WIP_ENTITY_ID
WHERE
    QR.QA_CREATION_DATE >= SYSDATE - 31
    AND QR.ORGANIZATION_ID = 1169
    AND QR.MAINTENANCE_OP_SEQ = 10
    AND EWO.WIP_ENTITY_NAME LIKE 'AU%'
ORDER BY
    QR.QA_CREATION_DATE DESC,
    QR.QA_LAST_UPDATE_DATE DESC;

SPOOL OFF
EXIT
```

### 23. QA results with group

**File:** `sql/qa_results_with_group.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists recent QA results enriched with active QA group membership.
**Parameters:** __DAYS__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, APPS.QA_RESULTS, APPS.QA_USER_GROUP_V

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    QUG.PERSON_NAME AS TECHNICIAN,
    QUG.USER_NAME AS BADGE_NUMBER,
    QUG.GROUP_NAME AS QA_GROUP,
    TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
    QR.CHARACTER1 AS LOT_NUMBER,
    QR.CHARACTER2 AS LOCATION,
    QR.CHARACTER3 AS REASON,
    QR.CHARACTER4 AS ADJUSTMENT,
    QR.COMMENT1 AS DESCRIPTION
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN APPS.QA_RESULTS QR
    ON QR.WORK_ORDER_ID = EWO.WIP_ENTITY_ID
   AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
JOIN APPS.QA_USER_GROUP_V QUG
    ON QUG.USER_ID = QR.QA_CREATED_BY
   AND QUG.STATUS = 'A'
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND QR.QA_CREATION_DATE >= SYSDATE - __DAYS__
ORDER BY QR.QA_CREATION_DATE DESC;

SPOOL OFF
EXIT
```

### 24. Released work orders for asset

**File:** `sql/released_work_orders_for_asset.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Lists released work orders for one asset.
**Parameters:** __ASSET_NUMBER__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    EWO.ASSET_ACTIVITY,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP AS WO_TYPE,
    TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY') AS CREATED,
    TO_CHAR(EWO.SCHEDULED_START_DATE, 'MM/DD/YYYY') AS SCHEDULED_START
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.ASSET_NUMBER = __ASSET_NUMBER__
  AND EWO.WORK_ORDER_STATUS = 'Released'
ORDER BY EWO.CREATION_DATE DESC;

SPOOL OFF
EXIT
```

### 25. Resource roster

**File:** `sql/resource_roster.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists every active person-type resource and currently assigned employee.
**Parameters:** __ORG_CODE__
**Referenced objects:** APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, BOM.BOM_RESOURCE_EMPLOYEES, BOM.BOM_RESOURCES

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    BR.RESOURCE_CODE,
    BR.DESCRIPTION AS RESOURCE_DESCRIPTION,
    BR.UNIT_OF_MEASURE,
    PEO.FULL_NAME,
    FU.USER_NAME AS BADGE_NUMBER,
    FU.EMAIL_ADDRESS,
    BRE.EFFECTIVE_START_DATE,
    BRE.EFFECTIVE_END_DATE
FROM BOM.BOM_RESOURCES BR
JOIN BOM.BOM_RESOURCE_EMPLOYEES BRE
    ON BRE.RESOURCE_ID = BR.RESOURCE_ID
   AND BRE.ORGANIZATION_ID = BR.ORGANIZATION_ID
JOIN APPS.PER_ALL_PEOPLE_F PEO
    ON PEO.PERSON_ID = BRE.PERSON_ID
   AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
LEFT JOIN APPS.FND_USER FU
    ON FU.EMPLOYEE_ID = PEO.PERSON_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = BR.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND BR.RESOURCE_TYPE = 2
  AND BR.DISABLE_DATE IS NULL
  AND SYSDATE <= BRE.EFFECTIVE_END_DATE
ORDER BY BR.RESOURCE_CODE, PEO.FULL_NAME;

SPOOL OFF
EXIT
```

### 26. Resources for employee

**File:** `sql/resources_for_employee.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists resources assigned to employees whose name matches a supplied search value.
**Parameters:** __NAME__, __ORG_CODE__
**Referenced objects:** APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, BOM.BOM_RESOURCE_EMPLOYEES, BOM.BOM_RESOURCES

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    PEO.FULL_NAME,
    BR.RESOURCE_CODE,
    BR.DESCRIPTION AS RESOURCE_DESCRIPTION,
    BR.UNIT_OF_MEASURE,
    BRE.EFFECTIVE_START_DATE,
    BRE.EFFECTIVE_END_DATE
FROM APPS.PER_ALL_PEOPLE_F PEO
JOIN BOM.BOM_RESOURCE_EMPLOYEES BRE
    ON BRE.PERSON_ID = PEO.PERSON_ID
   AND SYSDATE <= BRE.EFFECTIVE_END_DATE
JOIN BOM.BOM_RESOURCES BR
    ON BR.RESOURCE_ID = BRE.RESOURCE_ID
   AND BR.ORGANIZATION_ID = BRE.ORGANIZATION_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = BR.ORGANIZATION_ID
WHERE SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
  AND MP.ORGANIZATION_CODE = __ORG_CODE__
  AND UPPER(PEO.FULL_NAME) LIKE UPPER('%' || __NAME__ || '%')
ORDER BY PEO.FULL_NAME, BR.RESOURCE_CODE;

SPOOL OFF
EXIT
```

### 27. Technician productivity summary

**File:** `sql/technician_productivity_summary.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Ranks technicians by QA inspection volume, distinct work orders, and distinct assets over a rolling period.
**Parameters:** __LIMIT__, __MONTHS__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT *
FROM (
    SELECT
        PEO.FULL_NAME AS TECHNICIAN,
        FU.USER_NAME AS BADGE_NUMBER,
        COUNT(QR.ROWID) AS TOTAL_INSPECTIONS,
        COUNT(DISTINCT QR.WORK_ORDER_ID) AS UNIQUE_WORK_ORDERS,
        COUNT(DISTINCT EWO.ASSET_NUMBER) AS UNIQUE_ASSETS,
        MIN(QR.QA_CREATION_DATE) AS FIRST_INSPECTION,
        MAX(QR.QA_CREATION_DATE) AS LAST_INSPECTION
    FROM APPS.QA_RESULTS QR
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.WIP_ENTITY_ID = QR.WORK_ORDER_ID
       AND EWO.ORGANIZATION_ID = QR.ORGANIZATION_ID
    JOIN APPS.FND_USER FU
        ON FU.USER_ID = QR.QA_CREATED_BY
    JOIN APPS.PER_ALL_PEOPLE_F PEO
        ON PEO.PERSON_ID = FU.EMPLOYEE_ID
       AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = QR.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND QR.QA_CREATION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
    GROUP BY PEO.FULL_NAME, FU.USER_NAME
    ORDER BY TOTAL_INSPECTIONS DESC
)
WHERE ROWNUM <= __LIMIT__;

SPOOL OFF
EXIT
```

### 28. Top assets by time charged

**File:** `sql/top_assets_by_time_charged.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Ranks assets by actual HR time charged from WIP_TRANSACTIONS.
**Parameters:** __LIMIT__, __MONTHS__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, BOM.BOM_RESOURCES, WIP.WIP_TRANSACTIONS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT *
FROM (
    SELECT
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        COUNT(DISTINCT EWO.WIP_ENTITY_ID) AS WORK_ORDER_COUNT,
        COUNT(DISTINCT WT.OPERATION_SEQ_NUM) AS OPERATION_COUNT,
        COUNT(WT.ROWID) AS TIME_TRANSACTION_COUNT,
        SUM(WT.TRANSACTION_QUANTITY) AS TOTAL_TIME_CHARGED_HOURS,
        AVG(WT.TRANSACTION_QUANTITY) AS AVG_TIME_PER_TRANSACTION,
        RANK() OVER (ORDER BY SUM(WT.TRANSACTION_QUANTITY) DESC) AS RANK_BY_TIME_CHARGED
    FROM WIP.WIP_TRANSACTIONS WT
    JOIN APPS.EAM_WORK_ORDERS_V EWO
        ON EWO.WIP_ENTITY_ID = WT.WIP_ENTITY_ID
       AND EWO.ORGANIZATION_ID = WT.ORGANIZATION_ID
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    LEFT JOIN BOM.BOM_RESOURCES BR
        ON BR.RESOURCE_ID = WT.RESOURCE_ID
       AND BR.ORGANIZATION_ID = WT.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND EWO.ASSET_NUMBER IS NOT NULL
      AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -__MONTHS__)
      AND BR.UNIT_OF_MEASURE = 'HR'
    GROUP BY
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION
    ORDER BY
        TOTAL_TIME_CHARGED_HOURS DESC,
        WORK_ORDER_COUNT DESC,
        EWO.ASSET_NUMBER
)
WHERE ROWNUM <= __LIMIT__;

SPOOL OFF
EXIT
```

### 29. Top part transactions

**File:** `sql/top_part_transactions.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Finds work orders with the most part transactions in a recent rolling window.
**Parameters:** __DAYS__, __LIMIT__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, INV.MTL_MATERIAL_TRANSACTIONS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT *
FROM (
    SELECT
        EWO.WIP_ENTITY_NAME,
        EWO.ASSET_NUMBER,
        COUNT(MMT.TRANSACTION_ID) AS PART_TRANSACTIONS,
        SUM(ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST)) AS TOTAL_MATERIAL_COST
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
        ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
       AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
       AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND MMT.TRANSACTION_DATE >= SYSDATE - __DAYS__
    GROUP BY EWO.WIP_ENTITY_NAME, EWO.ASSET_NUMBER
    ORDER BY PART_TRANSACTIONS DESC, TOTAL_MATERIAL_COST DESC
)
WHERE ROWNUM <= __LIMIT__;

SPOOL OFF
EXIT
```

### 30. Top part transactions detail

**File:** `sql/top_part_transactions_detail.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Detail export for selected high-part-transaction work orders, including part cost and latest QA context.
**Parameters:** __DAYS__, __ORG_CODE__, __WORK_ORDER__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS, INV.MTL_MATERIAL_TRANSACTIONS, INV.MTL_SYSTEM_ITEMS_B, INV.MTL_TRANSACTION_TYPES

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH LATEST_QA AS (
    SELECT
        QR.ORGANIZATION_ID,
        QR.WORK_ORDER_ID,
        PEO.FULL_NAME AS TECHNICIAN,
        FU.USER_NAME AS BADGE_NUMBER,
        TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY QR.ORGANIZATION_ID, QR.WORK_ORDER_ID
            ORDER BY QR.QA_CREATION_DATE DESC
        ) AS RN
    FROM APPS.QA_RESULTS QR
    LEFT JOIN APPS.FND_USER FU
        ON FU.USER_ID = QR.QA_CREATED_BY
    LEFT JOIN APPS.PER_ALL_PEOPLE_F PEO
        ON PEO.PERSON_ID = FU.EMPLOYEE_ID
       AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
)
SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP AS WO_TYPE,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS WO_CREATED,
    LQ.TECHNICIAN,
    LQ.BADGE_NUMBER,
    LQ.INSPECTION_DATE AS LAST_INSPECTION_DATE,
    MTT.TRANSACTION_TYPE_NAME AS TRANSACTION_TYPE,
    TO_CHAR(MMT.TRANSACTION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS TRANSACTION_DATE,
    MSI.SEGMENT1 AS PART_NUMBER,
    MSI.DESCRIPTION AS PART_DESCRIPTION,
    MMT.TRANSACTION_QUANTITY AS QTY,
    ABS(MMT.TRANSACTION_QUANTITY) AS ABS_QTY,
    NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS UNIT_MATERIAL_COST,
    ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS LINE_MATERIAL_COST,
    MMT.TRANSACTION_UOM AS UOM,
    MMT.SUBINVENTORY_CODE AS FROM_SUBINVENTORY,
    MMT.TRANSACTION_REFERENCE AS REFERENCE
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
    ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
   AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
JOIN INV.MTL_SYSTEM_ITEMS_B MSI
    ON MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
   AND MSI.ORGANIZATION_ID = MMT.ORGANIZATION_ID
JOIN INV.MTL_TRANSACTION_TYPES MTT
    ON MTT.TRANSACTION_TYPE_ID = MMT.TRANSACTION_TYPE_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
LEFT JOIN LATEST_QA LQ
    ON LQ.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND LQ.WORK_ORDER_ID = EWO.WIP_ENTITY_ID
   AND LQ.RN = 1
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.WIP_ENTITY_NAME = __WORK_ORDER__
  AND MMT.TRANSACTION_DATE >= SYSDATE - __DAYS__
ORDER BY
    MMT.TRANSACTION_DATE DESC,
    MSI.SEGMENT1;

SPOOL OFF
EXIT
```

### 31. Top part transactions summary

**File:** `sql/top_part_transactions_summary.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Summary export for top part-transaction work orders with material cost and latest QA technician context.
**Parameters:** __DAYS__, __LIMIT__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS, INV.MTL_MATERIAL_TRANSACTIONS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

WITH LATEST_QA AS (
    SELECT
        QR.ORGANIZATION_ID,
        QR.WORK_ORDER_ID,
        PEO.FULL_NAME AS TECHNICIAN,
        FU.USER_NAME AS BADGE_NUMBER,
        TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
        ROW_NUMBER() OVER (
            PARTITION BY QR.ORGANIZATION_ID, QR.WORK_ORDER_ID
            ORDER BY QR.QA_CREATION_DATE DESC
        ) AS RN
    FROM APPS.QA_RESULTS QR
    LEFT JOIN APPS.FND_USER FU
        ON FU.USER_ID = QR.QA_CREATED_BY
    LEFT JOIN APPS.PER_ALL_PEOPLE_F PEO
        ON PEO.PERSON_ID = FU.EMPLOYEE_ID
       AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
),
WO_PARTS AS (
    SELECT
        EWO.ORGANIZATION_ID,
        EWO.WIP_ENTITY_ID,
        EWO.WIP_ENTITY_NAME AS WORK_ORDER,
        EWO.WORK_ORDER_STATUS,
        EWO.WORK_ORDER_TYPE_DISP AS WO_TYPE,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS WO_CREATED,
        COUNT(MMT.TRANSACTION_ID) AS PART_TRANSACTIONS,
        COUNT(DISTINCT MMT.INVENTORY_ITEM_ID) AS DISTINCT_PARTS_USED,
        SUM(CASE
                WHEN MMT.TRANSACTION_QUANTITY < 0
                THEN ABS(MMT.TRANSACTION_QUANTITY)
                ELSE 0
            END) AS TOTAL_PARTS_USED,
        SUM(CASE
                WHEN MMT.TRANSACTION_QUANTITY < 0
                THEN ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST)
                ELSE 0
            END) AS TOTAL_MATERIAL_COST
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
        ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
       AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
       AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
    JOIN APPS.MTL_PARAMETERS MP
        ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
      AND MMT.TRANSACTION_DATE >= SYSDATE - __DAYS__
    GROUP BY
        EWO.ORGANIZATION_ID,
        EWO.WIP_ENTITY_ID,
        EWO.WIP_ENTITY_NAME,
        EWO.WORK_ORDER_STATUS,
        EWO.WORK_ORDER_TYPE_DISP,
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS')
)
SELECT *
FROM (
    SELECT
        WP.WORK_ORDER,
        WP.WORK_ORDER_STATUS,
        WP.WO_TYPE,
        WP.ASSET_NUMBER,
        WP.ASSET_DESCRIPTION,
        WP.WO_CREATED,
        LQ.TECHNICIAN,
        LQ.BADGE_NUMBER,
        LQ.INSPECTION_DATE AS LAST_INSPECTION_DATE,
        WP.PART_TRANSACTIONS,
        WP.DISTINCT_PARTS_USED,
        WP.TOTAL_PARTS_USED,
        WP.TOTAL_MATERIAL_COST
    FROM WO_PARTS WP
    LEFT JOIN LATEST_QA LQ
        ON LQ.ORGANIZATION_ID = WP.ORGANIZATION_ID
       AND LQ.WORK_ORDER_ID = WP.WIP_ENTITY_ID
       AND LQ.RN = 1
    ORDER BY
        WP.PART_TRANSACTIONS DESC,
        WP.TOTAL_MATERIAL_COST DESC,
        WP.TOTAL_PARTS_USED DESC,
        WP.WORK_ORDER
)
WHERE ROWNUM <= __LIMIT__;

SPOOL OFF
EXIT
```

### 32. Top 10 assets work-order detail

**File:** `sql/top10_assets_wo_detail.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Ranks assets by work-order volume and returns detailed work-order, QA, and technician context.
**Parameters:** __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS, HR.HR_ALL_ORGANIZATION_UNITS

```sql
-- =============================================================
--  Top 10 Assets by Work Order Volume -- Last 12 Months
--
--  NOTE: __ORG_CODE__ is replaced by the Python runner before
--  this file is executed â€” do not edit that token directly.
--
--  Parameters:
--    &1 = output CSV file path (passed by SQLcl)
-- =============================================================

SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET DEFINE ON
SET SQLFORMAT CSV

SPOOL &1

WITH ORG AS (
    SELECT
        MP.ORGANIZATION_ID,
        MP.ORGANIZATION_CODE,
        HOU.NAME AS ORGANIZATION_NAME
    FROM APPS.MTL_PARAMETERS MP
    JOIN HR.HR_ALL_ORGANIZATION_UNITS HOU
        ON HOU.ORGANIZATION_ID = MP.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = '__ORG_CODE__'
      AND HOU.DATE_TO IS NULL
),
TOP_ASSETS AS (
    SELECT
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        ORG.ORGANIZATION_CODE,
        ORG.ORGANIZATION_NAME,
        ORG.ORGANIZATION_ID,
        COUNT(DISTINCT EWO.WIP_ENTITY_ID)  AS WORK_ORDER_COUNT,
        RANK() OVER (
            ORDER BY COUNT(DISTINCT EWO.WIP_ENTITY_ID) DESC
        )                                   AS ASSET_RANK
    FROM APPS.EAM_WORK_ORDERS_V EWO
    JOIN ORG ON ORG.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    WHERE
        EWO.ASSET_NUMBER  IS NOT NULL
        AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -12)
    GROUP BY
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        ORG.ORGANIZATION_CODE,
        ORG.ORGANIZATION_NAME,
        ORG.ORGANIZATION_ID
    ORDER BY WORK_ORDER_COUNT DESC
    FETCH FIRST 10 ROWS WITH TIES
)
SELECT
    TA.ORGANIZATION_CODE,
    TA.ORGANIZATION_NAME,
    TA.ASSET_RANK,
    TA.ASSET_NUMBER,
    TA.ASSET_DESCRIPTION,
    TA.WORK_ORDER_COUNT              AS TOTAL_WO_COUNT_12_MONTHS,
    EWO.WIP_ENTITY_NAME              AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP         AS WO_TYPE,
    EWO.ASSET_ACTIVITY,
    TO_CHAR(EWO.CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS') AS WO_CREATED_DATE,
    TO_CHAR(EWO.SCHEDULED_START_DATE,
            'MM/DD/YYYY')            AS SCHEDULED_START,
    PEO.FULL_NAME                    AS TECHNICIAN,
    FU.USER_NAME                     AS BADGE_NUMBER,
    TO_CHAR(QR.QA_CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
    QR.MAINTENANCE_OP_SEQ            AS OP_SEQ,
    QR.CHARACTER1                    AS LOT_NUMBER,
    QR.CHARACTER2                    AS LOCATION,
    QR.CHARACTER3                    AS REASON,
    QR.CHARACTER4                    AS ADJUSTMENT,
    QR.COMMENT1                      AS DESCRIPTION,
    EWO.DESCRIPTION                  AS WO_DESCRIPTION
FROM TOP_ASSETS TA
         JOIN APPS.EAM_WORK_ORDERS_V EWO
              ON  EWO.ASSET_NUMBER    = TA.ASSET_NUMBER
                  AND EWO.ORGANIZATION_ID = TA.ORGANIZATION_ID
                  AND EWO.CREATION_DATE  >= ADD_MONTHS(SYSDATE, -12)
         LEFT JOIN APPS.QA_RESULTS QR
                   ON  QR.WORK_ORDER_ID   = EWO.WIP_ENTITY_ID
                       AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         LEFT JOIN APPS.FND_USER FU
                   ON  FU.USER_ID         = QR.QA_CREATED_BY
         LEFT JOIN APPS.PER_ALL_PEOPLE_F PEO
                   ON  PEO.PERSON_ID      = FU.EMPLOYEE_ID
                       AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE
                           AND PEO.EFFECTIVE_END_DATE
ORDER BY
    TA.ASSET_RANK,
    TA.ASSET_NUMBER,
    EWO.CREATION_DATE DESC,
    QR.QA_CREATION_DATE DESC;

SPOOL OFF
EXIT
```

### 33. User responsibilities

**File:** `sql/user_responsibilities.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Lists responsibilities assigned to a supplied user. The `__IDENTIFIER__` value matches `FND_USER.USER_NAME`, `FND_USER.USER_ID`, or `FND_USER.EMPLOYEE_ID`/Oracle person ID; use `user_responsibilities_by_employee_number.sql` for visible HR employee numbers.
**Parameters:** __IDENTIFIER__
**Referenced objects:** APPS.FND_APPLICATION, APPS.FND_RESPONSIBILITY, APPS.FND_RESPONSIBILITY_TL, APPS.FND_USER, APPS.FND_USER_RESP_GROUPS_DIRECT

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    FU.USER_ID,
    FU.USER_NAME,
    FU.DESCRIPTION AS FULL_NAME,
    FU.EMAIL_ADDRESS,
    FU.EMPLOYEE_ID,
    FRT.RESPONSIBILITY_NAME,
    FA.APPLICATION_SHORT_NAME,
    FUR.START_DATE,
    FUR.END_DATE
FROM APPS.FND_USER FU
LEFT JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR
    ON FU.USER_ID = FUR.USER_ID
LEFT JOIN APPS.FND_RESPONSIBILITY FR
    ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
LEFT JOIN APPS.FND_RESPONSIBILITY_TL FRT
    ON FR.RESPONSIBILITY_ID = FRT.RESPONSIBILITY_ID
   AND FRT.LANGUAGE = 'US'
LEFT JOIN APPS.FND_APPLICATION FA
    ON FR.APPLICATION_ID = FA.APPLICATION_ID
WHERE FU.USER_NAME = __IDENTIFIER__
   OR TO_CHAR(FU.USER_ID) = __IDENTIFIER__
   OR TO_CHAR(FU.EMPLOYEE_ID) = __IDENTIFIER__
ORDER BY FRT.RESPONSIBILITY_NAME;

SPOOL OFF
EXIT
```

### 34. User responsibilities by employee number

**File:** `sql/user_responsibilities_by_employee_number.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists EAM responsibilities assigned to a visible HR employee number.
**Parameters:** __APP_SHORT_NAME__, __EMPLOYEE_NUMBER__
**Referenced objects:** APPS.FND_APPLICATION, APPS.FND_RESPONSIBILITY, APPS.FND_RESPONSIBILITY_TL, APPS.FND_USER, APPS.FND_USER_RESP_GROUPS_DIRECT, APPS.PER_ALL_PEOPLE_F

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    FU.USER_ID,
    FU.USER_NAME,
    FU.DESCRIPTION AS FULL_NAME,
    FU.EMAIL_ADDRESS,
    FU.EMPLOYEE_ID AS PERSON_ID,
    PEO.EMPLOYEE_NUMBER,
    PEO.FULL_NAME AS HR_FULL_NAME,
    FRT.RESPONSIBILITY_NAME,
    FA.APPLICATION_SHORT_NAME,
    FUR.START_DATE,
    FUR.END_DATE
FROM APPS.PER_ALL_PEOPLE_F PEO
JOIN APPS.FND_USER FU
    ON FU.EMPLOYEE_ID = PEO.PERSON_ID
LEFT JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR
    ON FU.USER_ID = FUR.USER_ID
LEFT JOIN APPS.FND_RESPONSIBILITY FR
    ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
LEFT JOIN APPS.FND_RESPONSIBILITY_TL FRT
    ON FR.RESPONSIBILITY_ID = FRT.RESPONSIBILITY_ID
   AND FRT.LANGUAGE = 'US'
LEFT JOIN APPS.FND_APPLICATION FA
    ON FR.APPLICATION_ID = FA.APPLICATION_ID
WHERE PEO.EMPLOYEE_NUMBER = __EMPLOYEE_NUMBER__
  AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
  AND FA.APPLICATION_SHORT_NAME = __APP_SHORT_NAME__
ORDER BY
    CASE WHEN FUR.END_DATE IS NULL THEN 0 ELSE 1 END,
    FRT.RESPONSIBILITY_NAME;

SPOOL OFF
EXIT
```

### 35. Users by responsibility

**File:** `sql/users_by_responsibility.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Lists active users assigned a supplied EAM responsibility.
**Parameters:** __APP_SHORT_NAME__, __RESPONSIBILITY_NAME__
**Referenced objects:** APPS.FND_APPLICATION, APPS.FND_RESPONSIBILITY, APPS.FND_RESPONSIBILITY_TL, APPS.FND_USER, APPS.FND_USER_RESP_GROUPS_DIRECT

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    FU.USER_NAME,
    FU.DESCRIPTION AS FULL_NAME,
    FU.EMAIL_ADDRESS,
    FUR.START_DATE,
    FUR.END_DATE
FROM APPS.FND_USER FU
JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR
    ON FUR.USER_ID = FU.USER_ID
JOIN APPS.FND_RESPONSIBILITY FR
    ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
JOIN APPS.FND_RESPONSIBILITY_TL FRT
    ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID
   AND FRT.LANGUAGE = 'US'
JOIN APPS.FND_APPLICATION FA
    ON FA.APPLICATION_ID = FR.APPLICATION_ID
WHERE FRT.RESPONSIBILITY_NAME = __RESPONSIBILITY_NAME__
  AND FA.APPLICATION_SHORT_NAME = __APP_SHORT_NAME__
  AND (FU.END_DATE IS NULL OR FU.END_DATE > SYSDATE)
ORDER BY FU.USER_NAME;

SPOOL OFF
EXIT
```

### 36. Verify EAM relationships

**File:** `sql/verify_eam_relationships.sql`
**Type:** SQL query
**Complexity:** Diagnostic
**Purpose:** PL/SQL diagnostic script that validates expected objects, joins, filters, and data-integrity assumptions.
**Parameters:** None
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_APPLICATION, APPS.FND_RESPONSIBILITY, APPS.FND_RESPONSIBILITY_TL, APPS.FND_USER, APPS.FND_USER_RESP_GROUPS_DIRECT, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS, APPS.WIP_OP_RESOURCE_INSTANCES_V, APPS.WIP_OPERATIONS_V, EAM.EAM_PM_SCHEDULING_RULES

```sql
-- =============================================================
--  EAM Relational Map â€” Verification Script
--  Schema: APPS | Org: 1169 | Org Code: XAU
--
--  Run with:  sqlcl user/pass@db @verify_eam_relationships.sql
--  Or:        sqlplus user/pass@db @verify_eam_relationships.sql
--
--  What this script does:
--    1. Confirms all tables/views are accessible
--    2. Confirms all documented columns exist
--    3. Validates each join relationship returns rows
--    4. Checks known filter values are present in the data
--    5. Flags any warnings (Cartesian risk, missing language rows, etc.)
-- =============================================================

SET SERVEROUTPUT ON SIZE UNLIMITED
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING OFF
SET PAGESIZE 0

DECLARE

    -- -------------------------------------------------------
    --  Counters
    -- -------------------------------------------------------
v_pass    NUMBER := 0;
    v_fail    NUMBER := 0;
    v_warn    NUMBER := 0;
    v_count   NUMBER;
    v_exists  NUMBER;

    -- -------------------------------------------------------
    --  Helpers
    -- -------------------------------------------------------
    PROCEDURE pass(p_msg VARCHAR2) IS
BEGIN
        DBMS_OUTPUT.PUT_LINE('  [PASS] ' || p_msg);
        v_pass := v_pass + 1;
END;

    PROCEDURE fail(p_msg VARCHAR2) IS
BEGIN
        DBMS_OUTPUT.PUT_LINE('  [FAIL] ' || p_msg);
        v_fail := v_fail + 1;
END;

    PROCEDURE warn(p_msg VARCHAR2) IS
BEGIN
        DBMS_OUTPUT.PUT_LINE('  [WARN] ' || p_msg);
        v_warn := v_warn + 1;
END;

    PROCEDURE section(p_title VARCHAR2) IS
BEGIN
        DBMS_OUTPUT.PUT_LINE('');
        DBMS_OUTPUT.PUT_LINE('----------------------------------------------');
        DBMS_OUTPUT.PUT_LINE(' ' || p_title);
        DBMS_OUTPUT.PUT_LINE('----------------------------------------------');
END;

    -- Check a table/view is accessible and has rows
    PROCEDURE check_table(p_owner VARCHAR2, p_table VARCHAR2) IS
        v_sql VARCHAR2(200);
BEGIN
SELECT COUNT(*) INTO v_exists
FROM all_objects
WHERE owner = UPPER(p_owner)
  AND object_name = UPPER(p_table)
  AND object_type IN ('TABLE','VIEW','SYNONYM');

IF v_exists = 0 THEN
            fail(p_owner || '.' || p_table || ' â€” not accessible');
ELSE
            v_sql := 'SELECT COUNT(*) FROM ' || p_owner || '.' || p_table || ' WHERE ROWNUM <= 1';
EXECUTE IMMEDIATE v_sql INTO v_count;
IF v_count > 0 THEN
                pass(p_owner || '.' || p_table || ' â€” accessible, has rows');
ELSE
                warn(p_owner || '.' || p_table || ' â€” accessible but EMPTY');
END IF;
END IF;
EXCEPTION WHEN OTHERS THEN
        fail(p_owner || '.' || p_table || ' â€” error: ' || SQLERRM);
END;

    -- Check a column exists on a table
    PROCEDURE check_col(p_owner VARCHAR2, p_table VARCHAR2, p_col VARCHAR2) IS
BEGIN
SELECT COUNT(*) INTO v_exists
FROM all_tab_columns
WHERE owner       = UPPER(p_owner)
  AND table_name  = UPPER(p_table)
  AND column_name = UPPER(p_col);

IF v_exists = 0 THEN
            fail(p_owner || '.' || p_table || '.' || p_col || ' â€” column NOT FOUND');
ELSE
            pass(p_owner || '.' || p_table || '.' || p_col || ' â€” column exists');
END IF;
END;

    -- Check a join returns at least one row
    PROCEDURE check_join(p_label VARCHAR2, p_sql VARCHAR2) IS
BEGIN
EXECUTE IMMEDIATE p_sql INTO v_count;
IF v_count > 0 THEN
            pass(p_label || ' â€” ' || v_count || ' row(s)');
ELSE
            warn(p_label || ' â€” join returned 0 rows (data may not exist yet)');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail(p_label || ' â€” SQL error: ' || SQLERRM);
END;

    -- Check a filter value exists
    PROCEDURE check_filter(p_label VARCHAR2, p_sql VARCHAR2) IS
BEGIN
EXECUTE IMMEDIATE p_sql INTO v_count;
IF v_count > 0 THEN
            pass(p_label || ' â€” found ' || v_count || ' match(es)');
ELSE
            warn(p_label || ' â€” 0 matches (filter value may be wrong or no data)');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail(p_label || ' â€” SQL error: ' || SQLERRM);
END;

BEGIN

    -- ===========================================================
    -- SECTION 1: TABLE / VIEW ACCESSIBILITY
    -- ===========================================================
section('1. TABLE & VIEW ACCESSIBILITY');

    check_table('APPS', 'EAM_WORK_ORDERS_V');
    check_table('APPS', 'QA_RESULTS');
    check_table('APPS', 'WIP_OPERATIONS_V');
    check_table('APPS', 'WIP_OP_RESOURCE_INSTANCES_V');
    check_table('APPS', 'MTL_PARAMETERS');
    check_table('APPS', 'FND_USER');
    check_table('APPS', 'PER_ALL_PEOPLE_F');
    check_table('APPS', 'FND_USER_RESP_GROUPS_DIRECT');
    check_table('APPS', 'FND_RESPONSIBILITY');
    check_table('APPS', 'FND_RESPONSIBILITY_TL');
    check_table('APPS', 'FND_APPLICATION');
    check_table('EAM',  'EAM_PM_SCHEDULING_RULES');


    -- ===========================================================
    -- SECTION 2: COLUMN EXISTENCE
    -- ===========================================================
section('2. COLUMN EXISTENCE');

    -- EAM_WORK_ORDERS_V
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'WIP_ENTITY_ID');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'WIP_ENTITY_NAME');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'ORGANIZATION_ID');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'WORK_ORDER_STATUS');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'USER_DEFINED_STATUS_ID');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'WORK_ORDER_TYPE_DISP');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'ASSET_NUMBER');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'ASSET_ACTIVITY');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'ASSET_DESCRIPTION');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'ASSET_GROUP_ID');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'CLASS_CODE');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'DESCRIPTION');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'CREATION_DATE');
    check_col('APPS', 'EAM_WORK_ORDERS_V', 'SCHEDULED_START_DATE');

    -- QA_RESULTS
    check_col('APPS', 'QA_RESULTS', 'WORK_ORDER_ID');
    check_col('APPS', 'QA_RESULTS', 'ORGANIZATION_ID');
    check_col('APPS', 'QA_RESULTS', 'QA_CREATED_BY');
    check_col('APPS', 'QA_RESULTS', 'QA_LAST_UPDATED_BY');
    check_col('APPS', 'QA_RESULTS', 'QA_CREATION_DATE');
    check_col('APPS', 'QA_RESULTS', 'QA_LAST_UPDATE_DATE');
    check_col('APPS', 'QA_RESULTS', 'MAINTENANCE_OP_SEQ');
    check_col('APPS', 'QA_RESULTS', 'PLAN_ID');
    check_col('APPS', 'QA_RESULTS', 'COLLECTION_ID');
    check_col('APPS', 'QA_RESULTS', 'OCCURRENCE');
    check_col('APPS', 'QA_RESULTS', 'STATUS');
    check_col('APPS', 'QA_RESULTS', 'CHARACTER1');
    check_col('APPS', 'QA_RESULTS', 'CHARACTER2');
    check_col('APPS', 'QA_RESULTS', 'CHARACTER3');
    check_col('APPS', 'QA_RESULTS', 'CHARACTER4');
    check_col('APPS', 'QA_RESULTS', 'COMMENT1');

    -- WIP_OPERATIONS_V
    check_col('APPS', 'WIP_OPERATIONS_V', 'WIP_ENTITY_ID');
    check_col('APPS', 'WIP_OPERATIONS_V', 'ORGANIZATION_ID');
    check_col('APPS', 'WIP_OPERATIONS_V', 'OPERATION_SEQ_NUM');
    check_col('APPS', 'WIP_OPERATIONS_V', 'OPERATION_COMPLETED');
    check_col('APPS', 'WIP_OPERATIONS_V', 'DEPARTMENT_CODE');

    -- WIP_OP_RESOURCE_INSTANCES_V
    check_col('APPS', 'WIP_OP_RESOURCE_INSTANCES_V', 'WIP_ENTITY_ID');
    check_col('APPS', 'WIP_OP_RESOURCE_INSTANCES_V', 'OPERATION_SEQ_NUM');
    check_col('APPS', 'WIP_OP_RESOURCE_INSTANCES_V', 'INSTANCE_NAME');

    -- MTL_PARAMETERS
    check_col('APPS', 'MTL_PARAMETERS', 'ORGANIZATION_ID');
    check_col('APPS', 'MTL_PARAMETERS', 'ORGANIZATION_CODE');

    -- FND_USER
    check_col('APPS', 'FND_USER', 'USER_ID');
    check_col('APPS', 'FND_USER', 'USER_NAME');
    check_col('APPS', 'FND_USER', 'DESCRIPTION');
    check_col('APPS', 'FND_USER', 'EMAIL_ADDRESS');
    check_col('APPS', 'FND_USER', 'EMPLOYEE_ID');
    check_col('APPS', 'FND_USER', 'END_DATE');

    -- PER_ALL_PEOPLE_F
    check_col('APPS', 'PER_ALL_PEOPLE_F', 'PERSON_ID');
    check_col('APPS', 'PER_ALL_PEOPLE_F', 'FULL_NAME');
    check_col('APPS', 'PER_ALL_PEOPLE_F', 'EFFECTIVE_START_DATE');
    check_col('APPS', 'PER_ALL_PEOPLE_F', 'EFFECTIVE_END_DATE');

    -- FND_USER_RESP_GROUPS_DIRECT
    check_col('APPS', 'FND_USER_RESP_GROUPS_DIRECT', 'USER_ID');
    check_col('APPS', 'FND_USER_RESP_GROUPS_DIRECT', 'RESPONSIBILITY_ID');
    check_col('APPS', 'FND_USER_RESP_GROUPS_DIRECT', 'START_DATE');
    check_col('APPS', 'FND_USER_RESP_GROUPS_DIRECT', 'END_DATE');

    -- FND_RESPONSIBILITY
    check_col('APPS', 'FND_RESPONSIBILITY', 'RESPONSIBILITY_ID');
    check_col('APPS', 'FND_RESPONSIBILITY', 'APPLICATION_ID');

    -- FND_RESPONSIBILITY_TL
    check_col('APPS', 'FND_RESPONSIBILITY_TL', 'RESPONSIBILITY_ID');
    check_col('APPS', 'FND_RESPONSIBILITY_TL', 'RESPONSIBILITY_NAME');
    check_col('APPS', 'FND_RESPONSIBILITY_TL', 'LANGUAGE');

    -- FND_APPLICATION
    check_col('APPS', 'FND_APPLICATION', 'APPLICATION_ID');
    check_col('APPS', 'FND_APPLICATION', 'APPLICATION_SHORT_NAME');

    -- EAM_PM_SCHEDULING_RULES
    check_col('EAM', 'EAM_PM_SCHEDULING_RULES', 'SCHEDULED_START_DATE');


    -- ===========================================================
    -- SECTION 3: JOIN RELATIONSHIP VALIDATION
    -- ===========================================================
section('3. JOIN RELATIONSHIP VALIDATION');

    -- QA_RESULTS â†’ EAM_WORK_ORDERS_V
    check_join(
        'QA_RESULTS â†’ EAM_WORK_ORDERS_V',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS QR
         JOIN APPS.EAM_WORK_ORDERS_V EWO
           ON QR.WORK_ORDER_ID   = EWO.WIP_ENTITY_ID
          AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- WIP_OPERATIONS_V â†’ EAM_WORK_ORDERS_V
    check_join(
        'WIP_OPERATIONS_V â†’ EAM_WORK_ORDERS_V',
        'SELECT COUNT(*) FROM APPS.WIP_OPERATIONS_V WO
         JOIN APPS.EAM_WORK_ORDERS_V EWO
           ON WO.WIP_ENTITY_ID   = EWO.WIP_ENTITY_ID
          AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         WHERE EWO.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- WIP_OP_RESOURCE_INSTANCES_V â†’ WIP_OPERATIONS_V â†’ EAM_WORK_ORDERS_V
    check_join(
        'WIP_OP_RESOURCE_INSTANCES_V â†’ WIP_OPERATIONS_V â†’ EAM_WORK_ORDERS_V',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN APPS.WIP_OPERATIONS_V WO
           ON WO.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
         JOIN APPS.WIP_OP_RESOURCE_INSTANCES_V RES
           ON RES.WIP_ENTITY_ID     = WO.WIP_ENTITY_ID
          AND RES.OPERATION_SEQ_NUM = WO.OPERATION_SEQ_NUM
         WHERE EWO.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- MTL_PARAMETERS â†’ EAM_WORK_ORDERS_V
    check_join(
        'MTL_PARAMETERS â†’ EAM_WORK_ORDERS_V (org 1169 / XAU)',
        'SELECT COUNT(*) FROM APPS.MTL_PARAMETERS MP
         JOIN APPS.EAM_WORK_ORDERS_V EWO
           ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         WHERE MP.ORGANIZATION_CODE = ''XAU''
           AND EWO.ORGANIZATION_ID  = 1169
           AND ROWNUM <= 100'
    );

    -- FND_USER â†’ PER_ALL_PEOPLE_F
    check_join(
        'FND_USER â†’ PER_ALL_PEOPLE_F (active employees)',
        'SELECT COUNT(*) FROM APPS.FND_USER FU
         JOIN APPS.PER_ALL_PEOPLE_F PEO
           ON PEO.PERSON_ID = FU.EMPLOYEE_ID
         WHERE SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE
                           AND PEO.EFFECTIVE_END_DATE
           AND FU.EMPLOYEE_ID IS NOT NULL
           AND ROWNUM <= 100'
    );

    -- QA_RESULTS â†’ FND_USER (created_by)
    check_join(
        'QA_RESULTS.QA_CREATED_BY â†’ FND_USER',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS QR
         JOIN APPS.FND_USER FU
           ON FU.USER_ID = QR.QA_CREATED_BY
         WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- QA_RESULTS â†’ FND_USER (last_updated_by)
    check_join(
        'QA_RESULTS.QA_LAST_UPDATED_BY â†’ FND_USER',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS QR
         JOIN APPS.FND_USER FU
           ON FU.USER_ID = QR.QA_LAST_UPDATED_BY
         WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- FND_USER â†’ FND_USER_RESP_GROUPS_DIRECT
    check_join(
        'FND_USER â†’ FND_USER_RESP_GROUPS_DIRECT',
        'SELECT COUNT(*) FROM APPS.FND_USER FU
         JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR
           ON FUR.USER_ID = FU.USER_ID
         WHERE ROWNUM <= 100'
    );

    -- FND_USER_RESP_GROUPS_DIRECT â†’ FND_RESPONSIBILITY
    check_join(
        'FND_USER_RESP_GROUPS_DIRECT â†’ FND_RESPONSIBILITY',
        'SELECT COUNT(*) FROM APPS.FND_USER_RESP_GROUPS_DIRECT FUR
         JOIN APPS.FND_RESPONSIBILITY FR
           ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
         WHERE ROWNUM <= 100'
    );

    -- FND_RESPONSIBILITY â†’ FND_RESPONSIBILITY_TL
    check_join(
        'FND_RESPONSIBILITY â†’ FND_RESPONSIBILITY_TL (LANGUAGE=US)',
        'SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY FR
         JOIN APPS.FND_RESPONSIBILITY_TL FRT
           ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID
          AND FRT.LANGUAGE = ''US''
         WHERE ROWNUM <= 100'
    );

    -- FND_RESPONSIBILITY â†’ FND_APPLICATION
    check_join(
        'FND_RESPONSIBILITY â†’ FND_APPLICATION',
        'SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY FR
         JOIN APPS.FND_APPLICATION FA
           ON FA.APPLICATION_ID = FR.APPLICATION_ID
         WHERE ROWNUM <= 100'
    );

    -- Full security chain
    check_join(
        'Full security chain: FND_USER â†’ RESP â†’ TL â†’ APPLICATION',
        'SELECT COUNT(*) FROM APPS.FND_USER FU
         JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR ON FUR.USER_ID = FU.USER_ID
         JOIN APPS.FND_RESPONSIBILITY FR            ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
         JOIN APPS.FND_RESPONSIBILITY_TL FRT        ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID
                                                   AND FRT.LANGUAGE = ''US''
         JOIN APPS.FND_APPLICATION FA               ON FA.APPLICATION_ID = FR.APPLICATION_ID
         WHERE (FU.END_DATE IS NULL OR FU.END_DATE > SYSDATE)
           AND ROWNUM <= 100'
    );


    -- ===========================================================
    -- SECTION 4: KNOWN FILTER VALUE VALIDATION
    -- ===========================================================
section('4. KNOWN FILTER VALUE VALIDATION');

    -- Org 1169 exists
    check_filter(
        'ORGANIZATION_ID = 1169 in MTL_PARAMETERS',
        'SELECT COUNT(*) FROM APPS.MTL_PARAMETERS
         WHERE ORGANIZATION_ID = 1169'
    );

    -- Org code XAU exists
    check_filter(
        'ORGANIZATION_CODE = ''XAU'' in MTL_PARAMETERS',
        'SELECT COUNT(*) FROM APPS.MTL_PARAMETERS
         WHERE ORGANIZATION_CODE = ''XAU'''
    );

    -- Org 1169 matches XAU
    check_filter(
        'Org 1169 maps to code XAU (consistency check)',
        'SELECT COUNT(*) FROM APPS.MTL_PARAMETERS
         WHERE ORGANIZATION_ID = 1169
           AND ORGANIZATION_CODE = ''XAU'''
    );

    -- Work orders exist for org 1169
    check_filter(
        'EAM work orders exist for org 1169',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V
         WHERE ORGANIZATION_ID = 1169 AND ROWNUM <= 1'
    );

    -- AU% work orders
    check_filter(
        'Work orders matching AU% exist',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V
         WHERE ORGANIZATION_ID = 1169
           AND WIP_ENTITY_NAME LIKE ''AU%'' AND ROWNUM <= 1'
    );

    -- PM% work orders
    check_filter(
        'Work orders matching PM% exist',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V
         WHERE ORGANIZATION_ID = 1169
           AND WIP_ENTITY_NAME LIKE ''PM%'' AND ROWNUM <= 1'
    );

    -- Released work orders
    check_filter(
        'Released work orders exist',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V
         WHERE ORGANIZATION_ID = 1169
           AND WORK_ORDER_STATUS = ''Released'' AND ROWNUM <= 1'
    );

    -- Cancelled work orders
    check_filter(
        'Cancelled work orders exist',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V
         WHERE ORGANIZATION_ID = 1169
           AND WORK_ORDER_STATUS = ''Cancelled'' AND ROWNUM <= 1'
    );

    -- USER_DEFINED_STATUS_ID = 3
    check_filter(
        'USER_DEFINED_STATUS_ID = 3 exists in EAM_WORK_ORDERS_V',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V
         WHERE ORGANIZATION_ID = 1169
           AND USER_DEFINED_STATUS_ID = 3 AND ROWNUM <= 1'
    );

    -- DM work order type
    check_filter(
        'WORK_ORDER_TYPE_DISP = ''DM'' exists',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V
         WHERE ORGANIZATION_ID = 1169
           AND WORK_ORDER_TYPE_DISP = ''DM'' AND ROWNUM <= 1'
    );

    -- OPERATION_SEQ_NUM = 10 in WIP_OPERATIONS_V
    check_filter(
        'OPERATION_SEQ_NUM = 10 in WIP_OPERATIONS_V',
        'SELECT COUNT(*) FROM APPS.WIP_OPERATIONS_V
         WHERE ORGANIZATION_ID = 1169
           AND OPERATION_SEQ_NUM = 10 AND ROWNUM <= 1'
    );

    -- QA results for org 1169
    check_filter(
        'QA_RESULTS rows exist for org 1169',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS
         WHERE ORGANIZATION_ID = 1169 AND ROWNUM <= 1'
    );

    -- MAINTENANCE_OP_SEQ = 10 in QA_RESULTS
    check_filter(
        'MAINTENANCE_OP_SEQ = 10 in QA_RESULTS',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS
         WHERE ORGANIZATION_ID = 1169
           AND MAINTENANCE_OP_SEQ = 10 AND ROWNUM <= 1'
    );

    -- EAM responsibility exists
    check_filter(
        'Responsibility ''ICU EAM Manager - XAU'' exists in FND_RESPONSIBILITY_TL',
        'SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY_TL
         WHERE RESPONSIBILITY_NAME = ''ICU EAM Manager - XAU''
           AND LANGUAGE = ''US'''
    );

    -- EAM application short name
    check_filter(
        'APPLICATION_SHORT_NAME = ''EAM'' exists in FND_APPLICATION',
        'SELECT COUNT(*) FROM APPS.FND_APPLICATION
         WHERE APPLICATION_SHORT_NAME = ''EAM'''
    );

    -- Active users with EAM Manager role
    check_filter(
        'Active users assigned ICU EAM Manager - XAU role',
        'SELECT COUNT(*) FROM APPS.FND_USER FU
         JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR ON FUR.USER_ID = FU.USER_ID
         JOIN APPS.FND_RESPONSIBILITY FR            ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
         JOIN APPS.FND_RESPONSIBILITY_TL FRT        ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID
                                                   AND FRT.LANGUAGE = ''US''
         JOIN APPS.FND_APPLICATION FA               ON FA.APPLICATION_ID = FR.APPLICATION_ID
         WHERE FRT.RESPONSIBILITY_NAME = ''ICU EAM Manager - XAU''
           AND FA.APPLICATION_SHORT_NAME = ''EAM''
           AND (FU.END_DATE IS NULL OR FU.END_DATE > SYSDATE)'
    );

    -- FND_RESPONSIBILITY_TL language row count (warn if only 1 language â€” expected)
BEGIN
SELECT COUNT(DISTINCT LANGUAGE) INTO v_count
FROM APPS.FND_RESPONSIBILITY_TL;
IF v_count >= 1 THEN
            pass('FND_RESPONSIBILITY_TL has ' || v_count || ' language(s) â€” LANGUAGE=US filter is required');
ELSE
            warn('FND_RESPONSIBILITY_TL language check â€” unexpected result');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail('FND_RESPONSIBILITY_TL language count â€” ' || SQLERRM);
END;


    -- ===========================================================
    -- SECTION 5: CARTESIAN / DATA INTEGRITY WARNINGS
    -- ===========================================================
section('5. DATA INTEGRITY & CARTESIAN RISK CHECKS');

    -- EAM_PM_SCHEDULING_RULES row count (should be small / single row)
BEGIN
SELECT COUNT(*) INTO v_count FROM EAM.EAM_PM_SCHEDULING_RULES;
IF v_count = 0 THEN
            warn('EAM_PM_SCHEDULING_RULES is EMPTY â€” Cartesian join in pm script will return 0 rows');
        ELSIF v_count = 1 THEN
            pass('EAM_PM_SCHEDULING_RULES has 1 row â€” Cartesian in pm script is safe');
ELSE
            warn('EAM_PM_SCHEDULING_RULES has ' || v_count
                 || ' rows â€” Cartesian join in pm_released_work_orders.sql will MULTIPLY results. Add an explicit join condition.');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail('EAM_PM_SCHEDULING_RULES row count â€” ' || SQLERRM);
END;

    -- PER_ALL_PEOPLE_F duplicates without date filter
BEGIN
SELECT COUNT(*) INTO v_count
FROM APPS.FND_USER FU
         JOIN APPS.PER_ALL_PEOPLE_F PEO ON PEO.PERSON_ID = FU.EMPLOYEE_ID
WHERE FU.EMPLOYEE_ID IS NOT NULL AND ROWNUM <= 500;

DECLARE v_filtered NUMBER;
BEGIN
SELECT COUNT(*) INTO v_filtered
FROM APPS.FND_USER FU
         JOIN APPS.PER_ALL_PEOPLE_F PEO ON PEO.PERSON_ID = FU.EMPLOYEE_ID
WHERE FU.EMPLOYEE_ID IS NOT NULL
  AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
  AND ROWNUM <= 500;

IF v_count > v_filtered THEN
                warn('PER_ALL_PEOPLE_F: unfiltered join returns ' || v_count
                     || ' rows vs ' || v_filtered
                     || ' with date filter â€” always use EFFECTIVE date range to prevent duplicates');
ELSE
                pass('PER_ALL_PEOPLE_F date filter check â€” no duplicates detected in sample');
END IF;
END;
EXCEPTION WHEN OTHERS THEN
        fail('PER_ALL_PEOPLE_F duplicate check â€” ' || SQLERRM);
END;

    -- QA_RESULTS subquery for user full name â€” verify it returns distinct single row
BEGIN
SELECT COUNT(*) INTO v_count
FROM (
         SELECT DISTINCT PEO.FULL_NAME
         FROM APPS.FND_USER FU
                  JOIN APPS.PER_ALL_PEOPLE_F PEO ON PEO.PERSON_ID = FU.EMPLOYEE_ID
         WHERE FU.USER_ID = (SELECT MIN(QA_CREATED_BY) FROM APPS.QA_RESULTS
                             WHERE ORGANIZATION_ID = 1169 AND ROWNUM <= 1)
           AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
     );
IF v_count = 1 THEN
            pass('User name subquery (QA_CREATED_BY â†’ FND_USER â†’ PER_ALL_PEOPLE_F) returns exactly 1 row');
        ELSIF v_count = 0 THEN
            warn('User name subquery returned 0 rows â€” employee record may be missing or inactive');
ELSE
            warn('User name subquery returned ' || v_count
                 || ' rows â€” DISTINCT is required, check date filter logic');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail('User name subquery check â€” ' || SQLERRM);
END;


    -- ===========================================================
    -- SUMMARY
    -- ===========================================================
section('SUMMARY');
    DBMS_OUTPUT.PUT_LINE('  PASSED  : ' || v_pass);
    DBMS_OUTPUT.PUT_LINE('  WARNINGS: ' || v_warn);
    DBMS_OUTPUT.PUT_LINE('  FAILED  : ' || v_fail);
    DBMS_OUTPUT.PUT_LINE('  TOTAL   : ' || (v_pass + v_warn + v_fail));
    DBMS_OUTPUT.PUT_LINE('');
    IF v_fail = 0 AND v_warn = 0 THEN
        DBMS_OUTPUT.PUT_LINE('  All checks passed. Schema is ready for queries.');
    ELSIF v_fail = 0 THEN
        DBMS_OUTPUT.PUT_LINE('  No failures. Review warnings before writing new queries.');
ELSE
        DBMS_OUTPUT.PUT_LINE('  Fix FAILED items before running production queries.');
END IF;
    DBMS_OUTPUT.PUT_LINE('');

END;
/
```

### 37. Verify org mapping

**File:** `sql/verify_org_mapping.sql`
**Type:** SQLcl CSV export
**Complexity:** Simple
**Purpose:** Confirms the organization ID/code mapping for a supplied organization code.
**Parameters:** __ORG_CODE__
**Referenced objects:** APPS.MTL_PARAMETERS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    ORGANIZATION_ID,
    ORGANIZATION_CODE
FROM APPS.MTL_PARAMETERS
WHERE ORGANIZATION_CODE = __ORG_CODE__;

SPOOL OFF
EXIT
```

### 38. Work order full picture

**File:** `sql/work_order_full_picture.sql`
**Type:** SQLcl CSV export
**Complexity:** Complex
**Purpose:** Wide work-order detail that combines operations, department, QA, technician, and parts transaction context.
**Parameters:** __ORG_CODE__, __WORK_ORDER__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.FND_USER, APPS.MTL_PARAMETERS, APPS.PER_ALL_PEOPLE_F, APPS.QA_RESULTS, APPS.WIP_OPERATIONS_V, BOM.BOM_DEPARTMENTS, INV.MTL_MATERIAL_TRANSACTIONS, INV.MTL_SYSTEM_ITEMS_B, INV.MTL_TRANSACTION_TYPES

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP AS WO_TYPE,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    EWO.ASSET_ACTIVITY,
    TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS WO_CREATED,
    TO_CHAR(EWO.SCHEDULED_START_DATE, 'MM/DD/YYYY') AS SCHEDULED_START,
    WO.OPERATION_SEQ_NUM AS OP_SEQ,
    WO.OPERATION_COMPLETED,
    BD.DEPARTMENT_CODE,
    PEO.FULL_NAME AS TECHNICIAN,
    FU.USER_NAME AS BADGE_NUMBER,
    TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
    QR.CHARACTER1 AS LOT_NUMBER,
    QR.CHARACTER2 AS LOCATION,
    QR.CHARACTER3 AS REASON,
    QR.CHARACTER4 AS ADJUSTMENT,
    QR.COMMENT1 AS DESCRIPTION,
    MSI.SEGMENT1 AS PART_NUMBER,
    MSI.DESCRIPTION AS PART_DESCRIPTION,
    MMT.TRANSACTION_QUANTITY AS PARTS_QTY,
    NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS PARTS_UNIT_MATERIAL_COST,
    ABS(MMT.TRANSACTION_QUANTITY) * NVL(MMT.TRANSACTION_COST, MMT.ACTUAL_COST) AS PARTS_LINE_MATERIAL_COST,
    MMT.TRANSACTION_UOM AS PARTS_UOM,
    MTT.TRANSACTION_TYPE_NAME AS PARTS_TRANSACTION_TYPE
FROM APPS.EAM_WORK_ORDERS_V EWO
LEFT JOIN APPS.WIP_OPERATIONS_V WO
    ON WO.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
   AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
LEFT JOIN BOM.BOM_DEPARTMENTS BD
    ON BD.DEPARTMENT_ID = WO.DEPARTMENT_ID
   AND BD.ORGANIZATION_ID = WO.ORGANIZATION_ID
LEFT JOIN APPS.QA_RESULTS QR
    ON QR.WORK_ORDER_ID = EWO.WIP_ENTITY_ID
   AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
LEFT JOIN APPS.FND_USER FU
    ON FU.USER_ID = QR.QA_CREATED_BY
LEFT JOIN APPS.PER_ALL_PEOPLE_F PEO
    ON PEO.PERSON_ID = FU.EMPLOYEE_ID
   AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
LEFT JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
    ON MMT.TRANSACTION_SOURCE_ID = EWO.WIP_ENTITY_ID
   AND MMT.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
LEFT JOIN INV.MTL_SYSTEM_ITEMS_B MSI
    ON MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
   AND MSI.ORGANIZATION_ID = MMT.ORGANIZATION_ID
LEFT JOIN INV.MTL_TRANSACTION_TYPES MTT
    ON MTT.TRANSACTION_TYPE_ID = MMT.TRANSACTION_TYPE_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.WIP_ENTITY_NAME = __WORK_ORDER__
ORDER BY WO.OPERATION_SEQ_NUM, QR.QA_CREATION_DATE DESC, MMT.TRANSACTION_DATE DESC;

SPOOL OFF
EXIT
```

### 39. Work order operations

**File:** `sql/work_order_operations.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists operations and department information for one work order.
**Parameters:** __ORG_CODE__, __WORK_ORDER__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, APPS.WIP_OPERATIONS_V, BOM.BOM_DEPARTMENTS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    WO.OPERATION_SEQ_NUM AS OP_SEQ,
    BD.DEPARTMENT_CODE,
    BD.DESCRIPTION AS DEPARTMENT_DESCRIPTION,
    WO.OPERATION_COMPLETED,
    WO.LAST_UPDATE_DATE
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN APPS.WIP_OPERATIONS_V WO
    ON WO.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
   AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
JOIN BOM.BOM_DEPARTMENTS BD
    ON BD.DEPARTMENT_ID = WO.DEPARTMENT_ID
   AND BD.ORGANIZATION_ID = WO.ORGANIZATION_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.WIP_ENTITY_NAME = __WORK_ORDER__
ORDER BY WO.OPERATION_SEQ_NUM;

SPOOL OFF
EXIT
```

### 40. Work order time charged

**File:** `sql/work_order_time_charged.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Aggregates actual charged time for a work order and operation sequence by department and resource.
**Parameters:** __OPERATION_SEQ__, __ORG_CODE__, __WORK_ORDER__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, APPS.WIP_OPERATIONS_V, BOM.BOM_DEPARTMENTS, BOM.BOM_RESOURCES, WIP.WIP_OPERATION_RESOURCES, WIP.WIP_TRANSACTIONS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    WT.OPERATION_SEQ_NUM,
    BD.DEPARTMENT_CODE,
    BD.DESCRIPTION AS DEPARTMENT_DESCRIPTION,
    BR.RESOURCE_CODE,
    BR.DESCRIPTION AS RESOURCE_DESCRIPTION,
    BR.UNIT_OF_MEASURE AS RESOURCE_UOM,
    WOR.USAGE_RATE_OR_AMOUNT AS PLANNED_QTY,
    WOR.APPLIED_RESOURCE_UNITS AS APPLIED_QTY,
    SUM(WT.TRANSACTION_QUANTITY) AS CHARGED_TIME_QTY
FROM WIP.WIP_TRANSACTIONS WT
JOIN APPS.EAM_WORK_ORDERS_V EWO
    ON EWO.WIP_ENTITY_ID = WT.WIP_ENTITY_ID
   AND EWO.ORGANIZATION_ID = WT.ORGANIZATION_ID
JOIN APPS.WIP_OPERATIONS_V WO
    ON WO.WIP_ENTITY_ID = WT.WIP_ENTITY_ID
   AND WO.ORGANIZATION_ID = WT.ORGANIZATION_ID
   AND WO.OPERATION_SEQ_NUM = WT.OPERATION_SEQ_NUM
LEFT JOIN BOM.BOM_DEPARTMENTS BD
    ON BD.DEPARTMENT_ID = WO.DEPARTMENT_ID
   AND BD.ORGANIZATION_ID = WO.ORGANIZATION_ID
LEFT JOIN BOM.BOM_RESOURCES BR
    ON BR.RESOURCE_ID = WT.RESOURCE_ID
   AND BR.ORGANIZATION_ID = WT.ORGANIZATION_ID
LEFT JOIN WIP.WIP_OPERATION_RESOURCES WOR
    ON WOR.WIP_ENTITY_ID = WT.WIP_ENTITY_ID
   AND WOR.ORGANIZATION_ID = WT.ORGANIZATION_ID
   AND WOR.OPERATION_SEQ_NUM = WT.OPERATION_SEQ_NUM
   AND WOR.RESOURCE_SEQ_NUM = WT.RESOURCE_SEQ_NUM
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND EWO.WIP_ENTITY_NAME = __WORK_ORDER__
  AND WT.OPERATION_SEQ_NUM = __OPERATION_SEQ__
GROUP BY
    EWO.WIP_ENTITY_NAME,
    EWO.WORK_ORDER_STATUS,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    WT.OPERATION_SEQ_NUM,
    BD.DEPARTMENT_CODE,
    BD.DESCRIPTION,
    BR.RESOURCE_CODE,
    BR.DESCRIPTION,
    BR.UNIT_OF_MEASURE,
    WOR.USAGE_RATE_OR_AMOUNT,
    WOR.APPLIED_RESOURCE_UNITS
ORDER BY
    WT.OPERATION_SEQ_NUM,
    BD.DEPARTMENT_CODE,
    BR.RESOURCE_CODE;

SPOOL OFF
EXIT
```

### 41. Work orders for department

**File:** `sql/work_orders_for_department.sql`
**Type:** SQLcl CSV export
**Complexity:** Medium
**Purpose:** Lists work orders whose operation 10 department matches a supplied department over a rolling day window.
**Parameters:** __DAYS__, __DEPARTMENT_CODE__, __ORG_CODE__
**Referenced objects:** APPS.EAM_WORK_ORDERS_V, APPS.MTL_PARAMETERS, APPS.WIP_OPERATIONS_V, BOM.BOM_DEPARTMENTS

```sql
SET ECHO OFF
SET FEEDBACK OFF
SET HEADING ON
SET PAGESIZE 0
SET LINESIZE 32767
SET TERMOUT OFF
SET VERIFY OFF
SET SQLFORMAT CSV

SPOOL &1

SELECT
    EWO.WIP_ENTITY_NAME AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP AS WO_TYPE,
    BD.DEPARTMENT_CODE,
    BD.DESCRIPTION AS DEPARTMENT_DESCRIPTION,
    WO.OPERATION_SEQ_NUM AS OP_SEQ,
    WO.OPERATION_COMPLETED,
    TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY') AS CREATED,
    TO_CHAR(EWO.SCHEDULED_START_DATE, 'MM/DD/YYYY') AS SCHEDULED_START
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN APPS.WIP_OPERATIONS_V WO
    ON WO.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
   AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
   AND WO.OPERATION_SEQ_NUM = 10
JOIN BOM.BOM_DEPARTMENTS BD
    ON BD.DEPARTMENT_ID = WO.DEPARTMENT_ID
   AND BD.ORGANIZATION_ID = WO.ORGANIZATION_ID
JOIN APPS.MTL_PARAMETERS MP
    ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE MP.ORGANIZATION_CODE = __ORG_CODE__
  AND BD.DEPARTMENT_CODE = __DEPARTMENT_CODE__
  AND EWO.CREATION_DATE >= SYSDATE - __DAYS__
ORDER BY EWO.CREATION_DATE DESC;

SPOOL OFF
EXIT
```
