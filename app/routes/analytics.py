"""
Analytics API Routes
Flask routes for WIP analytics dashboard
"""

from flask import Blueprint, jsonify, request, current_app, render_template
from pathlib import Path
from app.models.analytics import WIPAnalytics

bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@bp.route('/')
def index():
    """Analytics dashboard page"""
    return render_template('analytics.html')


@bp.route('/api/wip/<path:filepath>')
def analyze_wip_report(filepath):
    """
    Analyze a WIP report and return analytics data

    Example: GET /api/analytics/wip/qa_daily_results/report_20260202.xlsx
    """
    try:
        # Get file path
        output_dir = current_app.config['OUTPUT_BASE_DIR']
        file_path = output_dir / filepath

        # Security check
        try:
            file_path = file_path.resolve()
            output_dir = output_dir.resolve()
            file_path.relative_to(output_dir)
        except ValueError:
            return jsonify({'error': 'Invalid file path'}), 403

        # Check if file exists
        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        # Analyze the report
        analyzer = WIPAnalytics(str(file_path))
        analytics = analyzer.get_all_analytics()

        return jsonify(analytics)

    except Exception as e:
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 500


@bp.route('/api/wip/summary/<path:filepath>')
def get_wip_summary(filepath):
    """Get just summary statistics"""
    try:
        output_dir = current_app.config['OUTPUT_BASE_DIR']
        file_path = output_dir / filepath

        # Security check
        file_path = file_path.resolve()
        output_dir = output_dir.resolve()
        file_path.relative_to(output_dir)

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        analyzer = WIPAnalytics(str(file_path))
        summary = analyzer.get_summary_stats()

        return jsonify(summary)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/api/wip/chart/<chart_type>/<path:filepath>')
def get_chart_data(chart_type, filepath):
    """
    Get specific chart data

    chart_type: daily_trend, weekly_trend, monthly_trend, locations,
                assets, activities, users, reasons
    """
    try:
        output_dir = current_app.config['OUTPUT_BASE_DIR']
        file_path = output_dir / filepath

        # Security check
        file_path = file_path.resolve()
        output_dir = output_dir.resolve()
        file_path.relative_to(output_dir)

        if not file_path.exists():
            return jsonify({'error': 'File not found'}), 404

        analyzer = WIPAnalytics(str(file_path))

        # Get requested chart data
        chart_methods = {
            'daily_trend': analyzer.get_entities_by_date,
            'weekly_trend': analyzer.get_weekly_trend,
            'monthly_trend': analyzer.get_monthly_trend,
            'locations': analyzer.get_top_locations,
            'assets': analyzer.get_top_assets,
            'activities': analyzer.get_activity_breakdown,
            'users': analyzer.get_user_activity,
            'reasons': analyzer.get_reason_breakdown
        }

        if chart_type not in chart_methods:
            return jsonify({'error': 'Invalid chart type'}), 400

        data = chart_methods[chart_type]()

        return jsonify(data)

    except Exception as e:
        return jsonify({'error': str(e)}), 500