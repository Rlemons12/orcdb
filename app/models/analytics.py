from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


class WorkbookAnalytics:
    """Generate schema-aware analytics for every sheet in an Excel workbook."""

    def __init__(self, file_path: str | Path):
        self.file_path = Path(file_path)
        self.sheets = pd.read_excel(self.file_path, sheet_name=None)

    @staticmethod
    def _json_value(value: Any) -> Any:
        if pd.isna(value):
            return None
        if hasattr(value, "isoformat"):
            return value.isoformat()
        if hasattr(value, "item"):
            return value.item()
        return value

    @staticmethod
    def _date_columns(df: pd.DataFrame) -> list[str]:
        columns = []
        for column in df.columns:
            series = df[column]
            if pd.api.types.is_datetime64_any_dtype(series):
                columns.append(str(column))
                continue
            if pd.api.types.is_numeric_dtype(series):
                continue
            if any(token in str(column).upper() for token in ("DATE", "TIME", "MONTH")):
                converted = pd.to_datetime(series, errors="coerce")
                if len(series) and converted.notna().mean() >= 0.6:
                    columns.append(str(column))
        return columns

    def _analyze_sheet(self, name: str, df: pd.DataFrame) -> dict[str, Any]:
        df = df.dropna(how="all")
        numeric_columns = [
            str(column) for column in df.select_dtypes(include="number").columns
        ]
        date_columns = self._date_columns(df)
        categorical_columns = [
            str(column)
            for column in df.columns
            if str(column) not in numeric_columns and str(column) not in date_columns
        ]

        numeric_summary = []
        for column in numeric_columns[:12]:
            series = pd.to_numeric(df[column], errors="coerce").dropna()
            if series.empty:
                continue
            numeric_summary.append({
                "column": column,
                "count": int(series.count()),
                "sum": self._json_value(series.sum()),
                "average": self._json_value(series.mean()),
                "minimum": self._json_value(series.min()),
                "maximum": self._json_value(series.max()),
            })

        categorical_summary = []
        for column in categorical_columns[:12]:
            series = df[column].dropna().astype(str).str.strip()
            series = series[series != ""]
            if series.empty:
                continue
            counts = series.value_counts().head(10)
            categorical_summary.append({
                "column": column,
                "unique": int(series.nunique()),
                "values": [
                    {"label": label, "count": int(count)}
                    for label, count in counts.items()
                ],
            })

        date_trends = []
        for column in date_columns[:6]:
            dates = pd.to_datetime(df[column], errors="coerce").dropna()
            if dates.empty:
                continue
            counts = dates.dt.to_period("M").value_counts().sort_index()
            date_trends.append({
                "column": column,
                "start": dates.min().isoformat(),
                "end": dates.max().isoformat(),
                "values": [
                    {"label": str(period), "count": int(count)}
                    for period, count in counts.items()
                ],
            })

        preview = []
        for record in df.head(10).to_dict(orient="records"):
            preview.append({str(key): self._json_value(value) for key, value in record.items()})

        return {
            "name": name,
            "rows": int(len(df)),
            "columns": int(len(df.columns)),
            "column_names": [str(column) for column in df.columns],
            "numeric_summary": numeric_summary,
            "categorical_summary": categorical_summary,
            "date_trends": date_trends,
            "preview": preview,
        }

    def get_all_analytics(self) -> dict[str, Any]:
        sheets = [self._analyze_sheet(name, df) for name, df in self.sheets.items()]
        return {
            "file": self.file_path.name,
            "summary": {
                "sheet_count": len(sheets),
                "total_rows": sum(sheet["rows"] for sheet in sheets),
                "total_columns": sum(sheet["columns"] for sheet in sheets),
                "numeric_columns": sum(len(sheet["numeric_summary"]) for sheet in sheets),
                "categorical_columns": sum(len(sheet["categorical_summary"]) for sheet in sheets),
                "date_columns": sum(len(sheet["date_trends"]) for sheet in sheets),
            },
            "sheets": sheets,
        }


# Backward-compatible import for callers that used the old class name.
WIPAnalytics = WorkbookAnalytics
