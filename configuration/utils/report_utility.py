from pathlib import Path
import pandas as pd


class ReportUtility:
    @staticmethod
    def _autosize_worksheet(ws) -> None:
        for col in ws.columns:
            max_len = max(
                len(str(cell.value)) if cell.value else 0
                for cell in col
            )
            ws.column_dimensions[col[0].column_letter].width = max_len + 2

    @staticmethod
    def _dedupe_sheet_name(name: str, used_names: set[str]) -> str:
        cleaned = "".join(ch for ch in str(name) if ch not in '[]:*?/\\').strip()
        if not cleaned:
            cleaned = "Sheet"

        base = cleaned[:31]
        candidate = base
        suffix = 1
        while candidate in used_names:
            suffix_text = f"_{suffix}"
            candidate = f"{base[:31 - len(suffix_text)]}{suffix_text}"
            suffix += 1

        used_names.add(candidate)
        return candidate

    @staticmethod
    def csv_to_excel(
        csv_path: Path,
        excel_path: Path,
        sheet_name: str = "Report",
        freeze_header: bool = True,
        autosize_columns: bool = True,
    ) -> None:
        if not csv_path.exists():
            raise FileNotFoundError(csv_path)

        # Read clean CSV produced by SQLcl (SQLFORMAT CSV)
        df = pd.read_csv(csv_path)

        # Safety check: headers must exist
        if df.columns.isnull().any() or len(df.columns) == 0:
            raise ValueError(
                f"CSV appears to have no header row: {csv_path}"
            )

        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
            ws = writer.sheets[sheet_name]

            if freeze_header:
                ws.freeze_panes = "A2"

            if autosize_columns:
                ReportUtility._autosize_worksheet(ws)

    @staticmethod
    def dataframes_to_excel(
        sheets: list[tuple[str, pd.DataFrame]],
        excel_path: Path,
        freeze_header: bool = True,
        autosize_columns: bool = True,
    ) -> None:
        if not sheets:
            raise ValueError("At least one sheet is required")

        used_names: set[str] = set()
        with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
            for requested_name, df in sheets:
                sheet_name = ReportUtility._dedupe_sheet_name(requested_name, used_names)
                export_df = df if not df.empty else pd.DataFrame([{}])
                export_df.to_excel(writer, index=False, sheet_name=sheet_name)
                ws = writer.sheets[sheet_name]

                if freeze_header and ws.max_row > 1:
                    ws.freeze_panes = "A2"

                if autosize_columns:
                    ReportUtility._autosize_worksheet(ws)
