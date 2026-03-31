from pathlib import Path
import pandas as pd


class ReportUtility:
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
                for col in ws.columns:
                    max_len = max(
                        len(str(cell.value)) if cell.value else 0
                        for cell in col
                    )
                    ws.column_dimensions[col[0].column_letter].width = max_len + 2
