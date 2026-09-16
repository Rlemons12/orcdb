from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import pandas as pd

from app.models.analytics import WorkbookAnalytics
from app.services.report_catalog import build_script_arguments, get_report_catalog
from app import create_app


PROJECT_ROOT = Path(__file__).resolve().parent


class ApplicationRouteTests(unittest.TestCase):
    def test_main_pages_load(self):
        client = create_app().test_client()

        for path in ("/", "/dashboard", "/reports/", "/analytics/", "/contacts/"):
            with self.subTest(path=path):
                self.assertEqual(client.get(path).status_code, 200)


class ReportCatalogTests(unittest.TestCase):
    def test_catalog_scripts_exist(self):
        catalog = get_report_catalog(PROJECT_ROOT)
        self.assertGreater(len(catalog), 40)
        for report in catalog:
            self.assertTrue((PROJECT_ROOT / "scripts" / report["script"]).is_file())

    def test_required_arguments_are_validated(self):
        report = next(
            item for item in get_report_catalog(PROJECT_ROOT)
            if item["id"] == "lookup_user"
        )
        with self.assertRaisesRegex(ValueError, "Identifier is required"):
            build_script_arguments(report, {})
        self.assertEqual(
            build_script_arguments(report, {"identifier": "USER1"}),
            ["--identifier", "USER1"],
        )

    def test_qa_daily_report_includes_created_and_closed_times(self):
        sql = (PROJECT_ROOT / "sql" / "qa_daily_results_24_hours.sql").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "TO_CHAR(EWO.CREATION_DATE, 'MM/DD/YYYY HH24:MI:SS') "
            "AS WO_CREATED_DATE_TIME",
            sql,
        )
        self.assertIn(
            "TO_CHAR(EWO.DATE_COMPLETED, 'MM/DD/YYYY HH24:MI:SS') "
            "AS WO_CLOSED_DATE_TIME",
            sql,
        )


class WorkbookAnalyticsTests(unittest.TestCase):
    def test_analyzes_all_sheets_and_data_types(self):
        with TemporaryDirectory() as directory:
            workbook = Path(directory) / "sample.xlsx"
            with pd.ExcelWriter(workbook) as writer:
                pd.DataFrame({
                    "ASSET": ["A", "A", "B"],
                    "HOURS": [1.5, 2.5, 3.0],
                    "CREATION_DATE": pd.to_datetime(["2026-01-01", "2026-01-02", "2026-02-01"]),
                }).to_excel(writer, index=False, sheet_name="Detail")
                pd.DataFrame({"COUNT": [3]}).to_excel(writer, index=False, sheet_name="Summary")

            result = WorkbookAnalytics(workbook).get_all_analytics()
            self.assertEqual(result["summary"]["sheet_count"], 2)
            self.assertEqual(result["summary"]["total_rows"], 4)
            detail = next(sheet for sheet in result["sheets"] if sheet["name"] == "Detail")
            self.assertTrue(detail["numeric_summary"])
            self.assertTrue(detail["categorical_summary"])
            self.assertTrue(detail["date_trends"])


if __name__ == "__main__":
    unittest.main()
