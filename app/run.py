#!/usr/bin/env python3
"""
Flask application runner for Oracle DB Reporting System
"""

from app import create_app
import sys
from pathlib import Path

# Ensure configuration can be imported
sys.path.insert(0, str(Path(__file__).parent))

app = create_app()

print("\n=== Registered Routes ===")
for rule in app.url_map.iter_rules():
    print(rule, rule.methods)
print("=========================\n")

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("Oracle DB Reporting System - Web Interface")
    print("=" * 60)
    print("\nStarting Flask development server...")
    print("Access the application at: http://127.0.0.1:5010")
    print("\nKeyboard shortcuts:")
    print("  - Ctrl+G: Generate new report")
    print("  - ESC: Close modals")
    print("\nPress Ctrl+C to stop the server\n")

    app.run(
        host='0.0.0.0',
        port=5010,
        debug=True
    )