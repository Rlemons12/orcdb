-- =============================================================
--  EAM Relational Map — Verification Script
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
            fail(p_owner || '.' || p_table || ' — not accessible');
ELSE
            v_sql := 'SELECT COUNT(*) FROM ' || p_owner || '.' || p_table || ' WHERE ROWNUM <= 1';
EXECUTE IMMEDIATE v_sql INTO v_count;
IF v_count > 0 THEN
                pass(p_owner || '.' || p_table || ' — accessible, has rows');
ELSE
                warn(p_owner || '.' || p_table || ' — accessible but EMPTY');
END IF;
END IF;
EXCEPTION WHEN OTHERS THEN
        fail(p_owner || '.' || p_table || ' — error: ' || SQLERRM);
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
            fail(p_owner || '.' || p_table || '.' || p_col || ' — column NOT FOUND');
ELSE
            pass(p_owner || '.' || p_table || '.' || p_col || ' — column exists');
END IF;
END;

    -- Check a join returns at least one row
    PROCEDURE check_join(p_label VARCHAR2, p_sql VARCHAR2) IS
BEGIN
EXECUTE IMMEDIATE p_sql INTO v_count;
IF v_count > 0 THEN
            pass(p_label || ' — ' || v_count || ' row(s)');
ELSE
            warn(p_label || ' — join returned 0 rows (data may not exist yet)');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail(p_label || ' — SQL error: ' || SQLERRM);
END;

    -- Check a filter value exists
    PROCEDURE check_filter(p_label VARCHAR2, p_sql VARCHAR2) IS
BEGIN
EXECUTE IMMEDIATE p_sql INTO v_count;
IF v_count > 0 THEN
            pass(p_label || ' — found ' || v_count || ' match(es)');
ELSE
            warn(p_label || ' — 0 matches (filter value may be wrong or no data)');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail(p_label || ' — SQL error: ' || SQLERRM);
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

    -- QA_RESULTS → EAM_WORK_ORDERS_V
    check_join(
        'QA_RESULTS → EAM_WORK_ORDERS_V',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS QR
         JOIN APPS.EAM_WORK_ORDERS_V EWO
           ON QR.WORK_ORDER_ID   = EWO.WIP_ENTITY_ID
          AND QR.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- WIP_OPERATIONS_V → EAM_WORK_ORDERS_V
    check_join(
        'WIP_OPERATIONS_V → EAM_WORK_ORDERS_V',
        'SELECT COUNT(*) FROM APPS.WIP_OPERATIONS_V WO
         JOIN APPS.EAM_WORK_ORDERS_V EWO
           ON WO.WIP_ENTITY_ID   = EWO.WIP_ENTITY_ID
          AND WO.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         WHERE EWO.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- WIP_OP_RESOURCE_INSTANCES_V → WIP_OPERATIONS_V → EAM_WORK_ORDERS_V
    check_join(
        'WIP_OP_RESOURCE_INSTANCES_V → WIP_OPERATIONS_V → EAM_WORK_ORDERS_V',
        'SELECT COUNT(*) FROM APPS.EAM_WORK_ORDERS_V EWO
         JOIN APPS.WIP_OPERATIONS_V WO
           ON WO.WIP_ENTITY_ID = EWO.WIP_ENTITY_ID
         JOIN APPS.WIP_OP_RESOURCE_INSTANCES_V RES
           ON RES.WIP_ENTITY_ID     = WO.WIP_ENTITY_ID
          AND RES.OPERATION_SEQ_NUM = WO.OPERATION_SEQ_NUM
         WHERE EWO.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- MTL_PARAMETERS → EAM_WORK_ORDERS_V
    check_join(
        'MTL_PARAMETERS → EAM_WORK_ORDERS_V (org 1169 / XAU)',
        'SELECT COUNT(*) FROM APPS.MTL_PARAMETERS MP
         JOIN APPS.EAM_WORK_ORDERS_V EWO
           ON MP.ORGANIZATION_ID = EWO.ORGANIZATION_ID
         WHERE MP.ORGANIZATION_CODE = ''XAU''
           AND EWO.ORGANIZATION_ID  = 1169
           AND ROWNUM <= 100'
    );

    -- FND_USER → PER_ALL_PEOPLE_F
    check_join(
        'FND_USER → PER_ALL_PEOPLE_F (active employees)',
        'SELECT COUNT(*) FROM APPS.FND_USER FU
         JOIN APPS.PER_ALL_PEOPLE_F PEO
           ON PEO.PERSON_ID = FU.EMPLOYEE_ID
         WHERE SYSDATE BETWEEN PEO.EFFECTIVE_START_DATE
                           AND PEO.EFFECTIVE_END_DATE
           AND FU.EMPLOYEE_ID IS NOT NULL
           AND ROWNUM <= 100'
    );

    -- QA_RESULTS → FND_USER (created_by)
    check_join(
        'QA_RESULTS.QA_CREATED_BY → FND_USER',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS QR
         JOIN APPS.FND_USER FU
           ON FU.USER_ID = QR.QA_CREATED_BY
         WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- QA_RESULTS → FND_USER (last_updated_by)
    check_join(
        'QA_RESULTS.QA_LAST_UPDATED_BY → FND_USER',
        'SELECT COUNT(*) FROM APPS.QA_RESULTS QR
         JOIN APPS.FND_USER FU
           ON FU.USER_ID = QR.QA_LAST_UPDATED_BY
         WHERE QR.ORGANIZATION_ID = 1169 AND ROWNUM <= 100'
    );

    -- FND_USER → FND_USER_RESP_GROUPS_DIRECT
    check_join(
        'FND_USER → FND_USER_RESP_GROUPS_DIRECT',
        'SELECT COUNT(*) FROM APPS.FND_USER FU
         JOIN APPS.FND_USER_RESP_GROUPS_DIRECT FUR
           ON FUR.USER_ID = FU.USER_ID
         WHERE ROWNUM <= 100'
    );

    -- FND_USER_RESP_GROUPS_DIRECT → FND_RESPONSIBILITY
    check_join(
        'FND_USER_RESP_GROUPS_DIRECT → FND_RESPONSIBILITY',
        'SELECT COUNT(*) FROM APPS.FND_USER_RESP_GROUPS_DIRECT FUR
         JOIN APPS.FND_RESPONSIBILITY FR
           ON FR.RESPONSIBILITY_ID = FUR.RESPONSIBILITY_ID
         WHERE ROWNUM <= 100'
    );

    -- FND_RESPONSIBILITY → FND_RESPONSIBILITY_TL
    check_join(
        'FND_RESPONSIBILITY → FND_RESPONSIBILITY_TL (LANGUAGE=US)',
        'SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY FR
         JOIN APPS.FND_RESPONSIBILITY_TL FRT
           ON FRT.RESPONSIBILITY_ID = FR.RESPONSIBILITY_ID
          AND FRT.LANGUAGE = ''US''
         WHERE ROWNUM <= 100'
    );

    -- FND_RESPONSIBILITY → FND_APPLICATION
    check_join(
        'FND_RESPONSIBILITY → FND_APPLICATION',
        'SELECT COUNT(*) FROM APPS.FND_RESPONSIBILITY FR
         JOIN APPS.FND_APPLICATION FA
           ON FA.APPLICATION_ID = FR.APPLICATION_ID
         WHERE ROWNUM <= 100'
    );

    -- Full security chain
    check_join(
        'Full security chain: FND_USER → RESP → TL → APPLICATION',
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

    -- FND_RESPONSIBILITY_TL language row count (warn if only 1 language — expected)
BEGIN
SELECT COUNT(DISTINCT LANGUAGE) INTO v_count
FROM APPS.FND_RESPONSIBILITY_TL;
IF v_count >= 1 THEN
            pass('FND_RESPONSIBILITY_TL has ' || v_count || ' language(s) — LANGUAGE=US filter is required');
ELSE
            warn('FND_RESPONSIBILITY_TL language check — unexpected result');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail('FND_RESPONSIBILITY_TL language count — ' || SQLERRM);
END;


    -- ===========================================================
    -- SECTION 5: CARTESIAN / DATA INTEGRITY WARNINGS
    -- ===========================================================
section('5. DATA INTEGRITY & CARTESIAN RISK CHECKS');

    -- EAM_PM_SCHEDULING_RULES row count (should be small / single row)
BEGIN
SELECT COUNT(*) INTO v_count FROM EAM.EAM_PM_SCHEDULING_RULES;
IF v_count = 0 THEN
            warn('EAM_PM_SCHEDULING_RULES is EMPTY — Cartesian join in pm script will return 0 rows');
        ELSIF v_count = 1 THEN
            pass('EAM_PM_SCHEDULING_RULES has 1 row — Cartesian in pm script is safe');
ELSE
            warn('EAM_PM_SCHEDULING_RULES has ' || v_count
                 || ' rows — Cartesian join in pm_released_work_orders.sql will MULTIPLY results. Add an explicit join condition.');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail('EAM_PM_SCHEDULING_RULES row count — ' || SQLERRM);
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
                     || ' with date filter — always use EFFECTIVE date range to prevent duplicates');
ELSE
                pass('PER_ALL_PEOPLE_F date filter check — no duplicates detected in sample');
END IF;
END;
EXCEPTION WHEN OTHERS THEN
        fail('PER_ALL_PEOPLE_F duplicate check — ' || SQLERRM);
END;

    -- QA_RESULTS subquery for user full name — verify it returns distinct single row
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
            pass('User name subquery (QA_CREATED_BY → FND_USER → PER_ALL_PEOPLE_F) returns exactly 1 row');
        ELSIF v_count = 0 THEN
            warn('User name subquery returned 0 rows — employee record may be missing or inactive');
ELSE
            warn('User name subquery returned ' || v_count
                 || ' rows — DISTINCT is required, check date filter logic');
END IF;
EXCEPTION WHEN OTHERS THEN
        fail('User name subquery check — ' || SQLERRM);
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