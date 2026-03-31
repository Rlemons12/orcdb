from flask import Blueprint, render_template, current_app
from pathlib import Path
from datetime import datetime, timedelta
import os

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Dashboard homepage"""
    output_dir = current_app.config['OUTPUT_BASE_DIR']
    
    # Get recent reports from all categories
    recent_reports = get_recent_reports(output_dir, limit=10)
    
    # Get report statistics
    stats = get_report_statistics(output_dir)
    
    return render_template('index.html', 
                         recent_reports=recent_reports,
                         stats=stats)


@bp.route('/dashboard')
def dashboard():
    """Detailed dashboard view"""
    output_dir = current_app.config['OUTPUT_BASE_DIR']
    
    stats = get_report_statistics(output_dir)
    recent_by_type = get_reports_by_type(output_dir)
    
    return render_template('dashboard.html',
                         stats=stats,
                         reports_by_type=recent_by_type)


def get_recent_reports(base_dir: Path, limit: int = 10):
    """Get most recent reports across all categories"""
    reports = []
    
    if not base_dir.exists():
        return reports
    
    # Scan all subdirectories
    for category_dir in base_dir.iterdir():
        if not category_dir.is_dir():
            continue
            
        category_name = category_dir.name
        
        # Get Excel files
        for file_path in category_dir.glob("*.xlsx"):
            try:
                stat = file_path.stat()
                reports.append({
                    'name': file_path.name,
                    'category': format_category_name(category_name),
                    'path': file_path.relative_to(base_dir).as_posix(),
                    'size': format_file_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception:
                continue
    
    # Sort by modification time, newest first
    reports.sort(key=lambda x: x['modified'], reverse=True)
    
    return reports[:limit]


def get_report_statistics(base_dir: Path):
    """Calculate statistics about reports"""
    stats = {
        'total_reports': 0,
        'total_size': 0,
        'categories': 0,
        'today_count': 0,
        'week_count': 0,
    }
    
    if not base_dir.exists():
        return stats
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)
    
    categories = set()
    
    for category_dir in base_dir.iterdir():
        if not category_dir.is_dir():
            continue
        
        categories.add(category_dir.name)
        
        for file_path in category_dir.glob("*.xlsx"):
            try:
                stat = file_path.stat()
                stats['total_reports'] += 1
                stats['total_size'] += stat.st_size
                
                modified = datetime.fromtimestamp(stat.st_mtime)
                if modified >= today_start:
                    stats['today_count'] += 1
                if modified >= week_start:
                    stats['week_count'] += 1
            except Exception:
                continue
    
    stats['categories'] = len(categories)
    stats['total_size_str'] = format_file_size(stats['total_size'])
    
    return stats


def get_reports_by_type(base_dir: Path):
    """Get reports organized by category"""
    reports_by_type = {}
    
    if not base_dir.exists():
        return reports_by_type
    
    for category_dir in base_dir.iterdir():
        if not category_dir.is_dir():
            continue
        
        category_name = category_dir.name
        formatted_name = format_category_name(category_name)
        
        reports = []
        for file_path in category_dir.glob("*.xlsx"):
            try:
                stat = file_path.stat()
                reports.append({
                    'name': file_path.name,
                    'path': file_path.relative_to(base_dir).as_posix(),
                    'size': format_file_size(stat.st_size),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'modified_str': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            except Exception:
                continue
        
        # Sort by modification time
        reports.sort(key=lambda x: x['modified'], reverse=True)
        
        if reports:
            reports_by_type[formatted_name] = {
                'category_key': category_name,
                'count': len(reports),
                'reports': reports[:5]  # Show top 5
            }
    
    return reports_by_type


def format_category_name(category: str) -> str:
    """Format category directory name for display"""
    # Replace underscores with spaces and title case
    return category.replace('_', ' ').title()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"
