# Oracle EAM SQL Query Reference
**Schema:** `APPS` | **Org:** 1169 | **Org Code:** `XAU`

Queries organized from simplest to most complex.
All queries are read-only and scoped to org 1169 unless otherwise noted.

---

## Tier 1 — Single Table Lookups

### 1. Verify org code and ID mapping
```sql
SELECT ORGANIZATION_ID, ORGANIZATION_CODE
FROM APPS.MTL_PARAMETERS
WHERE ORGANIZATION_CODE = 'XAU';
```

---

### 2. Look up a user — by name, ID, or employee number
```sql
SELECT
    USER_ID,
    USER_NAME,
    DESCRIPTION        AS FULL_NAME,
    EMAIL_ADDRESS,
    EMPLOYEE_ID,
    END_DATE
FROM APPS.FND_USER
WHERE USER_NAME             = '10169062'
   OR TO_CHAR(USER_ID)      = '10169062'
   OR TO_CHAR(EMPLOYEE_ID)  = '10169062';
```

---

### 3. Find all active users with a specific EAM responsibility
```sql
SELECT
    FU.USER_NAME,
    FU.DESCRIPTION  AS FULL_NAME,
    FU.EMAIL_ADDRESS,
    FUR.START_DATE,
    FUR.END_DATE
FROM APPS.FND_USER FU
         JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR ON FUR.USER_ID = FU.USER_ID
         JOIN APPS.FND_RESPONSIBILITY FR            ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
         JOIN APPS.FND_RESPONSIBILITY_TL FRT        ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID
    AND FRT.LANGUAGE = 'US'
         JOIN APPS.FND_APPLICATION FA               ON FA.APPLICATION_ID = FR.APPLICATION_ID
WHERE FRT.RESPONSIBILITY_NAME  = 'ICU EAM Manager - XAU'
  AND FA.APPLICATION_SHORT_NAME = 'EAM'
  AND (FU.END_DATE IS NULL OR FU.END_DATE > SYSDATE)
ORDER BY FU.USER_NAME;
```

---

### 4. Find all responsibilities assigned to a specific user
```sql
SELECT
    FU.USER_ID,
    FU.USER_NAME,
    FU.DESCRIPTION          AS FULL_NAME,
    FU.EMAIL_ADDRESS,
    FU.EMPLOYEE_ID,
    FRT.RESPONSIBILITY_NAME,
    FA.APPLICATION_SHORT_NAME,
    FUR.START_DATE,
    FUR.END_DATE
FROM APPS.FND_USER FU
         LEFT JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR ON FU.USER_ID = FUR.USER_ID
         LEFT JOIN APPS.FND_RESPONSIBILITY FR            ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
         LEFT JOIN APPS.FND_RESPONSIBILITY_TL FRT        ON FR.RESPONSIBILITY_ID = FRT.RESPONSIBILITY_ID
    AND FRT.LANGUAGE = 'US'
         LEFT JOIN APPS.FND_APPLICATION FA               ON FR.APPLICATION_ID = FA.APPLICATION_ID
WHERE FU.USER_NAME            = '10169062'
   OR TO_CHAR(FU.USER_ID)     = '10169062'
   OR TO_CHAR(FU.EMPLOYEE_ID) = '10169062'
ORDER BY FRT.RESPONSIBILITY_NAME;
```

---

### 5. Find what QA groups a user belongs to
```sql
SELECT
    USER_ID,
    USER_NAME,
    PERSON_NAME,
    EMAIL_ADDRESS,
    GROUP_NAME,
    STATUS,
    LAST_UPDATE_DATE
FROM APPS.QA_USER_GROUP_V
WHERE USER_NAME = '10169062'   -- or: WHERE USER_ID = 35566
ORDER BY GROUP_NAME;
```

---

### 6. Find all members of a QA group
```sql
SELECT
    USER_NAME,
    PERSON_NAME,
    EMAIL_ADDRESS,
    GROUP_NAME,
    STATUS,
    LAST_UPDATE_DATE
FROM APPS.QA_USER_GROUP_V
WHERE GROUP_NAME = 'YOUR GROUP NAME'
  AND STATUS     = 'A'
ORDER BY PERSON_NAME;
```

---

### 7. List all released work orders for an asset
```sql
SELECT
    WIP_ENTITY_NAME         AS WORK_ORDER,
    ASSET_NUMBER,
    ASSET_DESCRIPTION,
    ASSET_ACTIVITY,
    WORK_ORDER_STATUS,
    WORK_ORDER_TYPE_DISP    AS WO_TYPE,
    TO_CHAR(CREATION_DATE,
            'MM/DD/YYYY')   AS CREATED,
    TO_CHAR(SCHEDULED_START_DATE,
            'MM/DD/YYYY')   AS SCHEDULED_START
FROM APPS.EAM_WORK_ORDERS_V
WHERE ORGANIZATION_ID    = 1169
  AND ASSET_NUMBER       = 'AU-AFL31600-00'
  AND WORK_ORDER_STATUS  = 'Released'
ORDER BY CREATION_DATE DESC;
```

---

### 8. List all cancelled work orders — last 15 days
```sql
SELECT
    WIP_ENTITY_NAME       AS WORK_ORDER,
    ASSET_NUMBER,
    ASSET_DESCRIPTION,
    ASSET_ACTIVITY,
    WORK_ORDER_STATUS,
    CLASS_CODE,
    TO_CHAR(CREATION_DATE,
            'MM/DD/YYYY') AS CREATED
FROM APPS.EAM_WORK_ORDERS_V
WHERE ORGANIZATION_ID   = 1169
  AND WORK_ORDER_STATUS = 'Cancelled'
  AND CREATION_DATE     >= SYSDATE - 15
ORDER BY CREATION_DATE DESC;
```

---

## Tier 2 — Two to Three Table Joins

### 9. QA results for a work order with technician name
```sql
SELECT
    EWO.WIP_ENTITY_NAME                         AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    PEO.FULL_NAME                               AS TECHNICIAN,
    FU.USER_NAME                                AS BADGE_NUMBER,
    TO_CHAR(QR.QA_CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS')            AS INSPECTION_DATE,
    QR.MAINTENANCE_OP_SEQ                       AS OP_SEQ,
    QR.CHARACTER1                               AS LOT_NUMBER,
    QR.CHARACTER2                               AS LOCATION,
    QR.CHARACTER3                               AS REASON,
    QR.CHARACTER4                               AS ADJUSTMENT,
    QR.COMMENT1                                 AS DESCRIPTION
FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN APPS.QA_RESULTS QR
              ON  QR.WORK_ORDER_ID   = EWO.WIP_ENTITY_ID
                  AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         JOIN APPS.FND_USER FU
              ON  FU.USER_ID         = QR.QA_CREATED_BY
         JOIN APPS.PER_ALL_PEOPLE_F PEO
              ON  PEO.PERSON_ID      = FU.EMPLOYEE_ID
                  AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
WHERE
    EWO.ORGANIZATION_ID  = 1169
  AND EWO.WIP_ENTITY_NAME = 'AU14857998'
ORDER BY QR.QA_CREATION_DATE DESC;
```

---

### 10. Parts charged to a work order
```sql
SELECT
    EWO.WIP_ENTITY_NAME                         AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    MTT.TRANSACTION_TYPE_NAME                   AS TRANSACTION_TYPE,
    TO_CHAR(MMT.TRANSACTION_DATE,
            'MM/DD/YYYY HH24:MI:SS')            AS TRANSACTION_DATE,
    MSI.SEGMENT1                                AS PART_NUMBER,
    MSI.DESCRIPTION                             AS PART_DESCRIPTION,
    MMT.TRANSACTION_QUANTITY                    AS QTY,
    MMT.TRANSACTION_UOM                         AS UOM,
    MMT.SUBINVENTORY_CODE                       AS FROM_SUBINVENTORY,
    MMT.TRANSACTION_REFERENCE                   AS REFERENCE
FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
              ON  MMT.TRANSACTION_SOURCE_ID      = EWO.WIP_ENTITY_ID
                  AND MMT.ORGANIZATION_ID            = EWO.ORGANIZATION_ID
                  AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
         JOIN INV.MTL_SYSTEM_ITEMS_B MSI
              ON  MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
                  AND MSI.ORGANIZATION_ID   = MMT.ORGANIZATION_ID
         JOIN INV.MTL_TRANSACTION_TYPES MTT
              ON  MTT.TRANSACTION_TYPE_ID = MMT.TRANSACTION_TYPE_ID
WHERE
    EWO.ORGANIZATION_ID   = 1169
  AND EWO.WIP_ENTITY_NAME = 'AU14857998'
ORDER BY MMT.TRANSACTION_DATE DESC;
```

---

### 11. Resources (equipment) assigned to an employee
```sql
SELECT
    PEO.FULL_NAME,
    BR.RESOURCE_CODE,
    BR.DESCRIPTION          AS RESOURCE_DESCRIPTION,
    BR.UNIT_OF_MEASURE,
    BRE.EFFECTIVE_START_DATE,
    BRE.EFFECTIVE_END_DATE
FROM APPS.PER_ALL_PEOPLE_F PEO
         JOIN BOM.BOM_RESOURCE_EMPLOYEES BRE
              ON  BRE.PERSON_ID       = PEO.PERSON_ID
                  AND SYSDATE            <= BRE.EFFECTIVE_END_DATE
         JOIN BOM.BOM_RESOURCES BR
              ON  BR.RESOURCE_ID      = BRE.RESOURCE_ID
                  AND BR.ORGANIZATION_ID  = BRE.ORGANIZATION_ID
WHERE
    SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
  AND BR.ORGANIZATION_ID = 1169
  AND UPPER(PEO.FULL_NAME) LIKE UPPER('%Smith%')
ORDER BY PEO.FULL_NAME, BR.RESOURCE_CODE;
```

---

### 12. Work order operations with department name
```sql
SELECT
    EWO.WIP_ENTITY_NAME         AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    WO.OPERATION_SEQ_NUM        AS OP_SEQ,
    BD.DEPARTMENT_CODE,
    BD.DESCRIPTION              AS DEPARTMENT_DESCRIPTION,
    WO.OPERATION_COMPLETED,
    WO.LAST_UPDATE_DATE
FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN APPS.WIP_OPERATIONS_V WO
              ON  WO.WIP_ENTITY_ID   = EWO.WIP_ENTITY_ID
                  AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         JOIN BOM.BOM_DEPARTMENTS BD
              ON  BD.DEPARTMENT_ID    = WO.DEPARTMENT_ID
                  AND BD.ORGANIZATION_ID  = WO.ORGANIZATION_ID
WHERE
    EWO.ORGANIZATION_ID  = 1169
  AND EWO.WIP_ENTITY_NAME = 'AU14857998'
ORDER BY WO.OPERATION_SEQ_NUM;
```

---

### 13. Open DM work orders at operation step 10 with assigned resource
```sql
SELECT DISTINCT
    EWO.WIP_ENTITY_NAME,
    EWO.WIP_ENTITY_ID,
    TO_CHAR(EWO.CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS')  AS CREATION_DATE_TIME,
    EWO.ASSET_NUMBER,
    EWO.WORK_ORDER_STATUS,
    WO.OPERATION_SEQ_NUM,
    WO.OPERATION_COMPLETED,
    RES.INSTANCE_NAME,
    EWO.DESCRIPTION
FROM APPS.WIP_OPERATIONS_V WO1
         JOIN APPS.EAM_WORK_ORDERS_V EWO
              ON  EWO.WIP_ENTITY_ID = WO1.WIP_ENTITY_ID
         JOIN APPS.WIP_OPERATIONS_V WO
              ON  EWO.WIP_ENTITY_ID = WO.WIP_ENTITY_ID
         JOIN APPS.WIP_OP_RESOURCE_INSTANCES_V RES
              ON  RES.WIP_ENTITY_ID     = EWO.WIP_ENTITY_ID
                  AND RES.OPERATION_SEQ_NUM = WO.OPERATION_SEQ_NUM
         JOIN APPS.MTL_PARAMETERS MP
              ON  MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
WHERE
    EWO.ORGANIZATION_ID       = 1169
  AND WO1.OPERATION_SEQ_NUM = 10
  AND WO.OPERATION_SEQ_NUM  = 10
  AND WO1.OPERATION_COMPLETED = 'N'
  AND EWO.USER_DEFINED_STATUS_ID = 3
  AND MP.ORGANIZATION_CODE   = 'XAU'
  AND EWO.WORK_ORDER_TYPE_DISP = 'DM'
  AND EWO.ASSET_NUMBER LIKE 'AU%'
ORDER BY CREATION_DATE_TIME ASC;
```

---

### 14. QA results enriched with QA group membership
```sql
SELECT
    EWO.WIP_ENTITY_NAME                     AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    QUG.PERSON_NAME                         AS TECHNICIAN,
    QUG.USER_NAME                           AS BADGE_NUMBER,
    QUG.GROUP_NAME                          AS QA_GROUP,
    TO_CHAR(QR.QA_CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS')        AS INSPECTION_DATE,
    QR.CHARACTER1                           AS LOT_NUMBER,
    QR.CHARACTER2                           AS LOCATION,
    QR.CHARACTER3                           AS REASON,
    QR.CHARACTER4                           AS ADJUSTMENT,
    QR.COMMENT1                             AS DESCRIPTION
FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN APPS.QA_RESULTS QR
              ON  QR.WORK_ORDER_ID   = EWO.WIP_ENTITY_ID
                  AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         JOIN APPS.QA_USER_GROUP_V QUG
              ON  QUG.USER_ID        = QR.QA_CREATED_BY
                  AND QUG.STATUS         = 'A'
WHERE
    EWO.ORGANIZATION_ID = 1169
  AND QR.QA_CREATION_DATE >= SYSDATE - 1
ORDER BY QR.QA_CREATION_DATE DESC;
```

---

### 15. All work orders completed by a named employee — rolling window
```sql
SELECT DISTINCT
    PEO.FULL_NAME,
    FU.USER_NAME                            AS BADGE_NUMBER,
    EWO.WIP_ENTITY_NAME                     AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.ASSET_NUMBER,
    EWO.ASSET_ACTIVITY,
    EWO.ASSET_DESCRIPTION,
    TO_CHAR(QR.QA_CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS')        AS INSPECTION_DATE,
    QR.CHARACTER1                           AS LOT_NUMBER,
    QR.CHARACTER2                           AS LOCATION,
    QR.CHARACTER3                           AS REASON,
    QR.CHARACTER4                           AS ADJUSTMENT,
    QR.COMMENT1                             AS DESCRIPTION
FROM APPS.PER_ALL_PEOPLE_F PEO
         JOIN APPS.FND_USER FU
              ON  FU.EMPLOYEE_ID     = PEO.PERSON_ID
         JOIN APPS.QA_RESULTS QR
              ON  QR.QA_CREATED_BY   = FU.USER_ID
                  AND QR.ORGANIZATION_ID = 1169
         JOIN APPS.EAM_WORK_ORDERS_V EWO
              ON  EWO.WIP_ENTITY_ID   = QR.WORK_ORDER_ID
                  AND EWO.ORGANIZATION_ID = QR.ORGANIZATION_ID
WHERE
    SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
  AND UPPER(PEO.FULL_NAME) LIKE UPPER('%Smith%')
  AND QR.QA_CREATION_DATE >= SYSDATE - 90
ORDER BY QR.QA_CREATION_DATE DESC;
```

---

### 16. Work orders with the most part transactions — last 30 days
```sql
SELECT DISTINCT
    EWO.WIP_ENTITY_NAME,
    EWO.ASSET_NUMBER,
    COUNT(MMT.TRANSACTION_ID) AS PART_TRANSACTIONS
FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
              ON  MMT.TRANSACTION_SOURCE_ID      = EWO.WIP_ENTITY_ID
                  AND MMT.ORGANIZATION_ID            = EWO.ORGANIZATION_ID
                  AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
WHERE
    EWO.ORGANIZATION_ID  = 1169
  AND MMT.TRANSACTION_DATE >= SYSDATE - 30
GROUP BY
    EWO.WIP_ENTITY_NAME,
    EWO.ASSET_NUMBER
ORDER BY PART_TRANSACTIONS DESC
    FETCH FIRST 10 ROWS ONLY;
```

---

## Tier 3 — Complex Queries (CTEs, Aggregations, Multi-source)

### 17. Top 10 assets by work order volume — last 12 months
Full ranking with all work order detail, QA results, and technician per asset:

```sql
WITH ORG AS (
    SELECT MP.ORGANIZATION_ID, MP.ORGANIZATION_CODE, HOU.NAME AS ORGANIZATION_NAME
    FROM APPS.MTL_PARAMETERS MP
             JOIN HR.HR_ALL_ORGANIZATION_UNITS HOU ON HOU.ORGANIZATION_ID = MP.ORGANIZATION_ID
    WHERE MP.ORGANIZATION_CODE = 'XAU' AND HOU.DATE_TO IS NULL
),
     TOP_ASSETS AS (
         SELECT
             EWO.ASSET_NUMBER,
             EWO.ASSET_DESCRIPTION,
             ORG.ORGANIZATION_CODE,
             ORG.ORGANIZATION_NAME,
             ORG.ORGANIZATION_ID,
             COUNT(DISTINCT EWO.WIP_ENTITY_ID) AS WORK_ORDER_COUNT,
             RANK() OVER (ORDER BY COUNT(DISTINCT EWO.WIP_ENTITY_ID) DESC) AS ASSET_RANK
         FROM APPS.EAM_WORK_ORDERS_V EWO
                  JOIN ORG ON ORG.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         WHERE EWO.ASSET_NUMBER IS NOT NULL
           AND EWO.CREATION_DATE >= ADD_MONTHS(SYSDATE, -12)
         GROUP BY EWO.ASSET_NUMBER, EWO.ASSET_DESCRIPTION,
                  ORG.ORGANIZATION_CODE, ORG.ORGANIZATION_NAME, ORG.ORGANIZATION_ID
         ORDER BY WORK_ORDER_COUNT DESC
             FETCH FIRST 10 ROWS WITH TIES
     )
SELECT
    TA.ORGANIZATION_CODE,
    TA.ASSET_RANK,
    TA.ASSET_NUMBER,
    TA.ASSET_DESCRIPTION,
    TA.WORK_ORDER_COUNT              AS TOTAL_WO_COUNT_12_MONTHS,
    EWO.WIP_ENTITY_NAME              AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP         AS WO_TYPE,
    TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS WO_CREATED_DATE,
    PEO.FULL_NAME                    AS TECHNICIAN,
    FU.USER_NAME                     AS BADGE_NUMBER,
    TO_CHAR(QR.QA_CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') AS INSPECTION_DATE,
    QR.CHARACTER1  AS LOT_NUMBER,
    QR.CHARACTER2  AS LOCATION,
    QR.CHARACTER3  AS REASON,
    QR.CHARACTER4  AS ADJUSTMENT,
    QR.COMMENT1    AS DESCRIPTION
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
                       AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
ORDER BY TA.ASSET_RANK, TA.ASSET_NUMBER, EWO.CREATION_DATE DESC;
```

---

### 18. Audit trail — quick version (everything a user touched)
```sql
SELECT *
FROM (
         SELECT
             'QA_RESULTS'           AS source_table,
             qr.work_order_id       AS entity_id,
             qr.qa_last_update_date AS change_date
         FROM APPS.QA_RESULTS qr
         WHERE qr.qa_last_updated_by = 35566
         UNION ALL
         SELECT
             'WIP_ENTITIES',
             we.wip_entity_id,
             we.last_update_date
         FROM APPS.WIP_ENTITIES we
         WHERE we.last_updated_by = 35566
         UNION ALL
         SELECT
             'WIP_OPERATIONS',
             wo.wip_entity_id,
             wo.last_update_date
         FROM APPS.WIP_OPERATIONS wo
         WHERE wo.last_updated_by = 35566
     )
ORDER BY change_date DESC;
```

---

### 19. Audit trail — full version (created and updated, with date filter)
```sql
SELECT *
FROM (
         SELECT
             'QA_RESULTS'        AS source_table,
             qr.work_order_id    AS entity_id,
             NVL(qr.qa_last_update_date, qr.qa_creation_date) AS change_date,
             CASE
                 WHEN qr.qa_created_by      = 35566 THEN 'CREATED'
                 WHEN qr.qa_last_updated_by = 35566 THEN 'UPDATED'
                 END AS action
         FROM APPS.QA_RESULTS qr
         WHERE 35566 IN (qr.qa_created_by, qr.qa_last_updated_by)
           AND NVL(qr.qa_last_update_date, qr.qa_creation_date)
             >= TO_DATE('25-JAN-2026','DD-MON-YYYY')
         UNION ALL
         SELECT
             'WIP_ENTITIES',
             we.wip_entity_id,
             NVL(we.last_update_date, we.creation_date),
             CASE
             WHEN we.created_by      = 35566 THEN 'CREATED'
             WHEN we.last_updated_by = 35566 THEN 'UPDATED'
             END
         FROM APPS.WIP_ENTITIES we
         WHERE 35566 IN (we.created_by, we.last_updated_by)
           AND NVL(we.last_update_date, we.creation_date)
             >= TO_DATE('25-JAN-2026','DD-MON-YYYY')
         UNION ALL
         SELECT
             'WIP_OPERATIONS',
             wo.wip_entity_id,
             wo.last_update_date,
             'UPDATED'
         FROM APPS.WIP_OPERATIONS wo
         WHERE wo.last_updated_by = 35566
           AND wo.last_update_date >= TO_DATE('25-JAN-2026','DD-MON-YYYY')
     )
ORDER BY change_date DESC;
```

---

### 20. Work order full picture — header + operations + QA + parts
Everything about a single work order in one query:

```sql
SELECT
    -- Work order header
    EWO.WIP_ENTITY_NAME                         AS WORK_ORDER,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP                    AS WO_TYPE,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    EWO.ASSET_ACTIVITY,
    TO_CHAR(EWO.CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS')            AS WO_CREATED,
    TO_CHAR(EWO.SCHEDULED_START_DATE,
            'MM/DD/YYYY')                       AS SCHEDULED_START,
    -- Operation
    WO.OPERATION_SEQ_NUM                        AS OP_SEQ,
    WO.OPERATION_COMPLETED,
    BD.DEPARTMENT_CODE,
    -- Technician
    PEO.FULL_NAME                               AS TECHNICIAN,
    FU.USER_NAME                                AS BADGE_NUMBER,
    -- QA results
    TO_CHAR(QR.QA_CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS')            AS INSPECTION_DATE,
    QR.CHARACTER1                               AS LOT_NUMBER,
    QR.CHARACTER2                               AS LOCATION,
    QR.CHARACTER3                               AS REASON,
    QR.CHARACTER4                               AS ADJUSTMENT,
    QR.COMMENT1                                 AS DESCRIPTION,
    -- Parts
    MSI.SEGMENT1                                AS PART_NUMBER,
    MSI.DESCRIPTION                             AS PART_DESCRIPTION,
    MMT.TRANSACTION_QUANTITY                    AS PARTS_QTY,
    MMT.TRANSACTION_UOM                         AS PARTS_UOM,
    MTT.TRANSACTION_TYPE_NAME                   AS PARTS_TRANSACTION_TYPE
FROM APPS.EAM_WORK_ORDERS_V EWO
-- Operations
         LEFT JOIN APPS.WIP_OPERATIONS_V WO
                   ON  WO.WIP_ENTITY_ID   = EWO.WIP_ENTITY_ID
                       AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
-- Department
         LEFT JOIN BOM.BOM_DEPARTMENTS BD
                   ON  BD.DEPARTMENT_ID   = WO.DEPARTMENT_ID
                       AND BD.ORGANIZATION_ID = WO.ORGANIZATION_ID
-- QA results
         LEFT JOIN APPS.QA_RESULTS QR
                   ON  QR.WORK_ORDER_ID   = EWO.WIP_ENTITY_ID
                       AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
-- Technician
         LEFT JOIN APPS.FND_USER FU
                   ON  FU.USER_ID         = QR.QA_CREATED_BY
         LEFT JOIN APPS.PER_ALL_PEOPLE_F PEO
                   ON  PEO.PERSON_ID      = FU.EMPLOYEE_ID
                       AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
-- Parts
         LEFT JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
                   ON  MMT.TRANSACTION_SOURCE_ID      = EWO.WIP_ENTITY_ID
                       AND MMT.ORGANIZATION_ID            = EWO.ORGANIZATION_ID
                       AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
         LEFT JOIN INV.MTL_SYSTEM_ITEMS_B MSI
                   ON  MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
                       AND MSI.ORGANIZATION_ID   = MMT.ORGANIZATION_ID
         LEFT JOIN INV.MTL_TRANSACTION_TYPES MTT
                   ON  MTT.TRANSACTION_TYPE_ID = MMT.TRANSACTION_TYPE_ID
WHERE
    EWO.ORGANIZATION_ID  = 1169
  AND EWO.WIP_ENTITY_NAME = 'AU14857998'
ORDER BY
    WO.OPERATION_SEQ_NUM,
    QR.QA_CREATION_DATE DESC,
    MMT.TRANSACTION_DATE DESC;
```

---

### 21. Asset reliability summary — work order frequency + parts volume
Ranks assets by total work orders and total parts consumed over the last 12 months:

```sql
WITH ASSET_WO AS (
    SELECT
        EWO.ASSET_NUMBER,
        EWO.ASSET_DESCRIPTION,
        COUNT(DISTINCT EWO.WIP_ENTITY_ID)   AS TOTAL_WORK_ORDERS,
        SUM(CASE WHEN EWO.WORK_ORDER_TYPE_DISP = 'DM'
                     THEN 1 ELSE 0 END)         AS DM_WORK_ORDERS,
        SUM(CASE WHEN EWO.WIP_ENTITY_NAME LIKE 'PM%'
                     THEN 1 ELSE 0 END)         AS PM_WORK_ORDERS
    FROM APPS.EAM_WORK_ORDERS_V EWO
    WHERE EWO.ORGANIZATION_ID = 1169
      AND EWO.ASSET_NUMBER   IS NOT NULL
      AND EWO.CREATION_DATE  >= ADD_MONTHS(SYSDATE, -12)
    GROUP BY EWO.ASSET_NUMBER, EWO.ASSET_DESCRIPTION
),
     ASSET_PARTS AS (
         SELECT
             EWO.ASSET_NUMBER,
             COUNT(MMT.TRANSACTION_ID)           AS TOTAL_PART_TRANSACTIONS,
             SUM(ABS(MMT.TRANSACTION_QUANTITY))  AS TOTAL_PARTS_CONSUMED
         FROM APPS.EAM_WORK_ORDERS_V EWO
                  JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
                       ON  MMT.TRANSACTION_SOURCE_ID      = EWO.WIP_ENTITY_ID
                           AND MMT.ORGANIZATION_ID            = EWO.ORGANIZATION_ID
                           AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
                           AND MMT.TRANSACTION_QUANTITY       < 0     -- issues only, not returns
         WHERE EWO.ORGANIZATION_ID = 1169
           AND MMT.TRANSACTION_DATE >= ADD_MONTHS(SYSDATE, -12)
         GROUP BY EWO.ASSET_NUMBER
     )
SELECT
    AW.ASSET_NUMBER,
    AW.ASSET_DESCRIPTION,
    AW.TOTAL_WORK_ORDERS,
    AW.DM_WORK_ORDERS,
    AW.PM_WORK_ORDERS,
    NVL(AP.TOTAL_PART_TRANSACTIONS, 0)  AS TOTAL_PART_TRANSACTIONS,
    NVL(AP.TOTAL_PARTS_CONSUMED, 0)     AS TOTAL_PARTS_CONSUMED,
    RANK() OVER (ORDER BY AW.TOTAL_WORK_ORDERS DESC) AS RANK_BY_WO,
    RANK() OVER (ORDER BY NVL(AP.TOTAL_PARTS_CONSUMED, 0) DESC) AS RANK_BY_PARTS
FROM ASSET_WO AW
         LEFT JOIN ASSET_PARTS AP ON AP.ASSET_NUMBER = AW.ASSET_NUMBER
ORDER BY AW.TOTAL_WORK_ORDERS DESC
    FETCH FIRST 20 ROWS ONLY;
```

---

### 22. Technician productivity summary — QA submissions per person
Ranks technicians by inspection volume over a rolling period:

```sql
SELECT
    PEO.FULL_NAME                               AS TECHNICIAN,
    FU.USER_NAME                                AS BADGE_NUMBER,
    COUNT(QR.ROWID)                             AS TOTAL_INSPECTIONS,
    COUNT(DISTINCT QR.WORK_ORDER_ID)            AS UNIQUE_WORK_ORDERS,
    COUNT(DISTINCT EWO.ASSET_NUMBER)            AS UNIQUE_ASSETS,
    MIN(QR.QA_CREATION_DATE)                    AS FIRST_INSPECTION,
    MAX(QR.QA_CREATION_DATE)                    AS LAST_INSPECTION
FROM APPS.QA_RESULTS QR
         JOIN APPS.EAM_WORK_ORDERS_V EWO
              ON  EWO.WIP_ENTITY_ID   = QR.WORK_ORDER_ID
                  AND EWO.ORGANIZATION_ID = QR.ORGANIZATION_ID
         JOIN APPS.FND_USER FU
              ON  FU.USER_ID          = QR.QA_CREATED_BY
         JOIN APPS.PER_ALL_PEOPLE_F PEO
              ON  PEO.PERSON_ID       = FU.EMPLOYEE_ID
                  AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
WHERE
    QR.ORGANIZATION_ID  = 1169
  AND QR.QA_CREATION_DATE >= ADD_MONTHS(SYSDATE, -3)
GROUP BY
    PEO.FULL_NAME,
    FU.USER_NAME
ORDER BY TOTAL_INSPECTIONS DESC
    FETCH FIRST 20 ROWS ONLY;
```

---

### 23. Parts consumption by asset — what parts does each asset use most
```sql
SELECT
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    MSI.SEGMENT1                                AS PART_NUMBER,
    MSI.DESCRIPTION                             AS PART_DESCRIPTION,
    COUNT(MMT.TRANSACTION_ID)                   AS TIMES_ISSUED,
    SUM(ABS(MMT.TRANSACTION_QUANTITY))          AS TOTAL_QTY_CONSUMED,
    MMT.TRANSACTION_UOM                         AS UOM
FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN INV.MTL_MATERIAL_TRANSACTIONS MMT
              ON  MMT.TRANSACTION_SOURCE_ID      = EWO.WIP_ENTITY_ID
                  AND MMT.ORGANIZATION_ID            = EWO.ORGANIZATION_ID
                  AND MMT.TRANSACTION_SOURCE_TYPE_ID = 5
                  AND MMT.TRANSACTION_QUANTITY       < 0      -- issues only
         JOIN INV.MTL_SYSTEM_ITEMS_B MSI
              ON  MSI.INVENTORY_ITEM_ID = MMT.INVENTORY_ITEM_ID
                  AND MSI.ORGANIZATION_ID   = MMT.ORGANIZATION_ID
WHERE
    EWO.ORGANIZATION_ID  = 1169
  AND EWO.ASSET_NUMBER = 'AU-AFL31600-00'
  AND MMT.TRANSACTION_DATE >= ADD_MONTHS(SYSDATE, -12)
GROUP BY
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    MSI.SEGMENT1,
    MSI.DESCRIPTION,
    MMT.TRANSACTION_UOM
ORDER BY TOTAL_QTY_CONSUMED DESC;
```

---

### 24. QA results — last 24 hours with technician and group
```sql
SELECT
    EWO.WIP_ENTITY_NAME                         AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    QUG.PERSON_NAME                             AS TECHNICIAN,
    QUG.USER_NAME                               AS BADGE_NUMBER,
    QUG.GROUP_NAME                              AS QA_GROUP,
    TO_CHAR(QR.QA_CREATION_DATE,
            'MM/DD/YYYY HH24:MI:SS')            AS INSPECTION_DATE,
    QR.CHARACTER1                               AS LOT_NUMBER,
    QR.CHARACTER2                               AS LOCATION,
    QR.CHARACTER3                               AS REASON,
    QR.CHARACTER4                               AS ADJUSTMENT,
    QR.COMMENT1                                 AS DESCRIPTION
FROM APPS.QA_RESULTS QR
JOIN APPS.EAM_WORK_ORDERS_V EWO
    ON  EWO.WIP_ENTITY_ID   = QR.WORK_ORDER_ID
    AND EWO.ORGANIZATION_ID = QR.ORGANIZATION_ID
JOIN APPS.QA_USER_GROUP_V QUG
    ON  QUG.USER_ID         = QR.QA_CREATED_BY
    AND QUG.STATUS          = 'A'
WHERE
    QR.ORGANIZATION_ID    = 1169
    AND QR.QA_CREATION_DATE >= SYSDATE - 1
ORDER BY QR.QA_CREATION_DATE DESC;
```

---

### 25. Released PM work orders — currently open
```sql
SELECT
    EWO.WIP_ENTITY_NAME                         AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    EWO.ASSET_ACTIVITY,
    EWO.WORK_ORDER_STATUS,
    EWO.CLASS_CODE,
    TO_CHAR(EWO.CREATION_DATE,
            'MM/DD/YYYY')                       AS CREATED,
    TO_CHAR(EWO.SCHEDULED_START_DATE,
            'MM/DD/YYYY')                       AS SCHEDULED_START,
    EWO.DESCRIPTION                             AS WO_DESCRIPTION
FROM APPS.EAM_WORK_ORDERS_V EWO
WHERE
    EWO.ORGANIZATION_ID    = 1169
    AND EWO.WIP_ENTITY_NAME LIKE 'PM%'
    AND EWO.WORK_ORDER_STATUS = 'Released'
ORDER BY EWO.SCHEDULED_START_DATE ASC;
```

---

### 26. All employees assigned to a specific resource (reverse of Q11)
Given a resource code, find who is assigned to it:

```sql
SELECT
    BR.RESOURCE_CODE,
    BR.DESCRIPTION          AS RESOURCE_DESCRIPTION,
    BR.RESOURCE_TYPE,
    PEO.FULL_NAME,
    FU.USER_NAME            AS BADGE_NUMBER,
    FU.EMAIL_ADDRESS,
    BRE.EFFECTIVE_START_DATE,
    BRE.EFFECTIVE_END_DATE
FROM BOM.BOM_RESOURCES BR
JOIN BOM.BOM_RESOURCE_EMPLOYEES BRE
    ON  BRE.RESOURCE_ID     = BR.RESOURCE_ID
    AND BRE.ORGANIZATION_ID = BR.ORGANIZATION_ID
JOIN APPS.PER_ALL_PEOPLE_F PEO
    ON  PEO.PERSON_ID       = BRE.PERSON_ID
    AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
LEFT JOIN APPS.FND_USER FU
    ON  FU.EMPLOYEE_ID      = PEO.PERSON_ID
WHERE
    BR.ORGANIZATION_ID   = 1169
    AND BR.RESOURCE_CODE = 'YOUR-RESOURCE-CODE'   -- replace with resource code
    AND SYSDATE         <= BRE.EFFECTIVE_END_DATE
ORDER BY PEO.FULL_NAME;
```

---

### 27. All work orders for a department — last 90 days
Find all work orders where the primary operation belongs to a specific department:

```sql
SELECT
    EWO.WIP_ENTITY_NAME                         AS WORK_ORDER,
    EWO.ASSET_NUMBER,
    EWO.ASSET_DESCRIPTION,
    EWO.WORK_ORDER_STATUS,
    EWO.WORK_ORDER_TYPE_DISP                    AS WO_TYPE,
    BD.DEPARTMENT_CODE,
    BD.DESCRIPTION                              AS DEPARTMENT_DESCRIPTION,
    WO.OPERATION_SEQ_NUM                        AS OP_SEQ,
    WO.OPERATION_COMPLETED,
    TO_CHAR(EWO.CREATION_DATE,
            'MM/DD/YYYY')                       AS CREATED,
    TO_CHAR(EWO.SCHEDULED_START_DATE,
            'MM/DD/YYYY')                       AS SCHEDULED_START
FROM APPS.EAM_WORK_ORDERS_V EWO
JOIN APPS.WIP_OPERATIONS_V WO
    ON  WO.WIP_ENTITY_ID   = EWO.WIP_ENTITY_ID
    AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
    AND WO.OPERATION_SEQ_NUM = 10
JOIN BOM.BOM_DEPARTMENTS BD
    ON  BD.DEPARTMENT_ID   = WO.DEPARTMENT_ID
    AND BD.ORGANIZATION_ID = WO.ORGANIZATION_ID
WHERE
    EWO.ORGANIZATION_ID  = 1169
    AND BD.DEPARTMENT_CODE = 'YOUR-DEPT-CODE'   -- replace with department code
    AND EWO.CREATION_DATE >= SYSDATE - 90
ORDER BY EWO.CREATION_DATE DESC;
```

---

### 28. All resources and their currently assigned employees — full roster
Lists every active Person-type resource with all employees currently assigned:

```sql
SELECT
    BR.RESOURCE_CODE,
    BR.DESCRIPTION          AS RESOURCE_DESCRIPTION,
    BR.UNIT_OF_MEASURE,
    PEO.FULL_NAME,
    FU.USER_NAME            AS BADGE_NUMBER,
    FU.EMAIL_ADDRESS,
    BRE.EFFECTIVE_START_DATE,
    BRE.EFFECTIVE_END_DATE
FROM BOM.BOM_RESOURCES BR
JOIN BOM.BOM_RESOURCE_EMPLOYEES BRE
    ON  BRE.RESOURCE_ID     = BR.RESOURCE_ID
    AND BRE.ORGANIZATION_ID = BR.ORGANIZATION_ID
JOIN APPS.PER_ALL_PEOPLE_F PEO
    ON  PEO.PERSON_ID       = BRE.PERSON_ID
    AND SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE AND PEO.EFFECTIVE_END_DATE
LEFT JOIN APPS.FND_USER FU
    ON  FU.EMPLOYEE_ID      = PEO.PERSON_ID
WHERE
    BR.ORGANIZATION_ID  = 1169
    AND BR.RESOURCE_TYPE = 2              -- Person resources only
    AND BR.DISABLE_DATE IS NULL           -- Active resources only
    AND SYSDATE        <= BRE.EFFECTIVE_END_DATE
ORDER BY BR.RESOURCE_CODE, PEO.FULL_NAME;
```

---

## Quick Reference

| # | Query | Tables | Complexity |
|---|-------|--------|------------|
| 1 | Verify org code | MTL_PARAMETERS | Simple |
| 2 | Look up a user | FND_USER | Simple |
| 3 | Active users with EAM responsibility | FND_USER + 4 joins | Simple |
| 4 | All responsibilities for a user | FND_USER + 4 joins | Simple |
| 5 | QA groups for a user | QA_USER_GROUP_V | Simple |
| 6 | All members of a QA group | QA_USER_GROUP_V | Simple |
| 7 | Released work orders for an asset | EAM_WORK_ORDERS_V | Simple |
| 8 | Cancelled work orders last 15 days | EAM_WORK_ORDERS_V | Simple |
| 9 | QA results with technician name | EAM_WORK_ORDERS_V + QA_RESULTS + FND_USER + PER_ALL_PEOPLE_F | Medium |
| 10 | Parts charged to a work order | EAM_WORK_ORDERS_V + MTL_MATERIAL_TRANSACTIONS + MTL_SYSTEM_ITEMS_B + MTL_TRANSACTION_TYPES | Medium |
| 11 | Resources assigned to an employee | PER_ALL_PEOPLE_F + BOM_RESOURCE_EMPLOYEES + BOM_RESOURCES | Medium |
| 12 | Work order operations with department | EAM_WORK_ORDERS_V + WIP_OPERATIONS_V + BOM_DEPARTMENTS | Medium |
| 13 | Open DM work orders at step 10 | EAM_WORK_ORDERS_V + WIP_OPERATIONS_V + WIP_OP_RESOURCE_INSTANCES_V + MTL_PARAMETERS | Medium |
| 14 | QA results with QA group | EAM_WORK_ORDERS_V + QA_RESULTS + QA_USER_GROUP_V | Medium |
| 15 | Work orders completed by an employee | PER_ALL_PEOPLE_F + FND_USER + QA_RESULTS + EAM_WORK_ORDERS_V | Medium |
| 16 | Work orders with most part transactions | EAM_WORK_ORDERS_V + MTL_MATERIAL_TRANSACTIONS | Medium |
| 17 | Top 10 assets by work order volume | CTE + 6 tables | Complex |
| 18 | Audit trail — quick | QA_RESULTS + WIP_ENTITIES + WIP_OPERATIONS | Complex |
| 19 | Audit trail — full with date filter | QA_RESULTS + WIP_ENTITIES + WIP_OPERATIONS | Complex |
| 20 | Work order full picture | 8 tables, all LEFT JOINs | Complex |
| 21 | Asset reliability summary | CTE + EAM_WORK_ORDERS_V + MTL_MATERIAL_TRANSACTIONS | Complex |
| 22 | Technician productivity summary | QA_RESULTS + EAM_WORK_ORDERS_V + FND_USER + PER_ALL_PEOPLE_F | Complex |
| 23 | Parts consumption by asset | EAM_WORK_ORDERS_V + MTL_MATERIAL_TRANSACTIONS + MTL_SYSTEM_ITEMS_B | Complex |
| 24 | QA results last 24 hours with technician and group | QA_RESULTS + EAM_WORK_ORDERS_V + QA_USER_GROUP_V | Medium |
| 25 | Released PM work orders — currently open | EAM_WORK_ORDERS_V | Simple |
| 26 | All employees assigned to a resource (reverse lookup) | BOM_RESOURCES + BOM_RESOURCE_EMPLOYEES + PER_ALL_PEOPLE_F + FND_USER | Medium |
| 27 | All work orders for a department | EAM_WORK_ORDERS_V + WIP_OPERATIONS_V + BOM_DEPARTMENTS | Medium |
| 28 | Full resource roster — all active Person resources | BOM_RESOURCES + BOM_RESOURCE_EMPLOYEES + PER_ALL_PEOPLE_F + FND_USER | Medium |