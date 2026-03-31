from flask import Blueprint, render_template, current_app, send_file, abort, jsonify
from pathlib import Path
from datetime import datetime
import os

bp = Blueprint('reports', __name__, url_prefix='/reports')


@bp.route('/')
def index():
    """Browse all reports"""
    output_dir = current_app.config['OUTPUT_BASE_DIR']
    
    # Get all reports organized by category
    reports_by_category = get_all_reports(output_dir)
    
    return render_template('reports/index.html', 
                         reports_by_category=reports_by_category)


@bp.route('/category/<category>')
def category(category):
    """View reports in a specific category"""
    output_dir = current_app.config['OUTPUT_BASE_DIR']
    category_dir = output_dir / category
    
    if not category_dir.exists() or not category_dir.is_dir():
        abort(404)
    
    reports = get_category_reports(category_dir)
    
    return render_template('reports/category.html',
                         category=format_category_name(category),
                         category_key=category,
                         reports=reports)


@bp.route('/download/<path:filepath>')
def download(filepath):
    """Download a report file"""
    output_dir = current_app.config['OUTPUT_BASE_DIR']
    file_path = output_dir / filepath
    
    # Security check: ensure file is within output directory
    try:
        file_path = file_path.resolve()
        output_dir = output_dir.resolve()
        file_path.relative_to(output_dir)
    except ValueError:
        abort(403)
    
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file_path.name
    )


@bp.route('/preview/<path:filepath>')
def preview(filepath):
    """Preview report metadata"""
    output_dir = current_app.config['OUTPUT_BASE_DIR']
    file_path = output_dir / filepath
    
    # Security check
    try:
        file_path = file_path.resolve()
        output_dir = output_dir.resolve()
        file_path.relative_to(output_dir)
    except ValueError:
        abort(403)
    
    if not file_path.exists() or not file_path.is_file():
        abort(404)
    
    # Get file metadata
    stat = file_path.stat()
    metadata = {
        'name': file_path.name,
        'size': format_file_size(stat.st_size),
        'size_bytes': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
        'category': file_path.parent.name,
        'path': filepath
    }
    
    return render_template('reports/preview.html', 
                         file=metadata)


def get_all_reports(base_dir: Path):
    """Get all reports organized by category"""
    reports_by_category = {}
    
    if not base_dir.exists():
        return reports_by_category
    
    for category_dir in base_dir.iterdir():
        if not category_dir.is_dir():
            continue
        
        category_name = category_dir.name
        reports = get_category_reports(category_dir)
        
        if reports:
            reports_by_category[format_category_name(category_name)] = {
                'category_key': category_name,
                'count': len(reports),
                'reports': reports
            }
    
    return reports_by_category


def get_category_reports(category_dir: Path):
    """Get all reports in a category"""
    reports = []
    
    for file_path in category_dir.glob("*.xlsx"):
        try:
            stat = file_path.stat()
            reports.append({
                'name': file_path.name,
                'path': str(file_path.relative_to(category_dir.parent)),
                'size': format_file_size(stat.st_size),
                'size_bytes': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        except Exception:
            continue
    
    # Sort by modification time, newest first
    reports.sort(key=lambda x: x['modified'], reverse=True)
    
    return reports


def format_category_name(category: str) -> str:
    """Format category directory name for display"""
    return category.replace('_', ' ').title()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
