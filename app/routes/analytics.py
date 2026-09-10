from __future__ import annotations

from datetime import datetime

from flask import Blueprint, current_app, jsonify, render_template

from app.models.analytics import WorkbookAnalytics


bp = Blueprint("analytics", __name__, url_prefix="/analytics")


def _resolve_report(filepath: str):
    output_dir = current_app.config["OUTPUT_BASE_DIR"].resolve()
    file_path = (output_dir / filepath).resolve()
    file_path.relative_to(output_dir)
    if not file_path.is_file() or file_path.suffix.lower() != ".xlsx":
        raise FileNotFoundError(filepath)
    return file_path


@bp.route("/")
def index():
    return render_template("analytics.html")


@bp.route("/api/reports")
def available_reports():
    output_dir = current_app.config["OUTPUT_BASE_DIR"]
    reports = []
    if output_dir.exists():
        for path in output_dir.rglob("*.xlsx"):
            if path.name.startswith("~$"):
                continue
            try:
                stat = path.stat()
                reports.append({
                    "path": path.relative_to(output_dir).as_posix(),
                    "name": path.name,
                    "category": path.parent.name,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "size": stat.st_size,
                })
            except OSError:
                continue
    reports.sort(key=lambda item: item["modified"], reverse=True)
    return jsonify(reports)


@bp.route("/api/workbook/<path:filepath>")
def analyze_workbook(filepath):
    try:
        analytics = WorkbookAnalytics(_resolve_report(filepath)).get_all_analytics()
        return jsonify(analytics)
    except ValueError:
        return jsonify({"error": "Invalid file path"}), 403
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404
    except Exception as exc:
        current_app.logger.exception("Workbook analysis failed")
        return jsonify({"error": "Analysis failed", "message": str(exc)}), 500


@bp.route("/api/wip/<path:filepath>")
def analyze_wip_report(filepath):
    return analyze_workbook(filepath)
