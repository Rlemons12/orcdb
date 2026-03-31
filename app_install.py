#!/usr/bin/env python3
"""
Oracle DB Reporting System - ONE CLICK INSTALLER
Extracts and sets up the complete frontend automatically.
"""

import os
import sys
import zipfile
import tarfile
from pathlib import Path

print("=" * 70)
print("Oracle DB Reporting System - ONE CLICK INSTALLER")
print("=" * 70)

BASE_DIR = Path.cwd()
SCRIPT_DIR = Path(__file__).parent.resolve()

print(f"\nInstallation directory: {BASE_DIR}")
print(f"Installer location: {SCRIPT_DIR}\n")

# Look for the archive file
archive_files = [
    SCRIPT_DIR / "frontend_files.tar.gz",
    SCRIPT_DIR / "frontend_files.zip",
    BASE_DIR / "frontend_files.tar.gz",
    BASE_DIR / "frontend_files.zip",
]

archive_path = None
for af in archive_files:
    if af.exists():
        archive_path = af
        break

if not archive_path:
    print("ERROR: Could not find frontend_files.tar.gz or frontend_files.zip")
    print("\nPlease ensure the archive file is in the same directory as this installer.")
    print("\nExpected files:")
    print("  - frontend_files.tar.gz  OR")
    print("  - frontend_files.zip")
    input("\nPress Enter to exit...")
    sys.exit(1)

print(f"Found archive: {archive_path.name}\n")
print("This will extract:")
print("  ✓ app/ folder (Flask application)")
print("  ✓ HTML templates")
print("  ✓ CSS and JavaScript")
print("  ✓ Python backend files")
print("  ✓ Documentation\n")

response = input("Install now? (yes/no): ").strip().lower()
if response not in ['yes', 'y']:
    print("Installation cancelled.")
    input("\nPress Enter to exit...")
    sys.exit(0)

print("\n" + "=" * 70)
print("Extracting files...")
print("=" * 70)

try:
    # Extract based on file type
    if archive_path.suffix == '.gz':
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(BASE_DIR)
            members = tar.getnames()
    else:  # .zip
        with zipfile.ZipFile(archive_path, 'r') as zip_ref:
            zip_ref.extractall(BASE_DIR)
            members = zip_ref.namelist()

    print(f"✓ Extracted {len(members)} files\n")

    # Show what was extracted
    print("Key files installed:")
    important_files = ['app/', 'run_app.py', 'requirements.txt', 'README.md']
    for item in important_files:
        if any(item in m for m in members):
            print(f"  ✓ {item}")

    print("\n" + "=" * 70)
    print("Installation Complete!")
    print("=" * 70)

    print("\nNext steps:")
    print("\n1. Install dependencies:")
    print("   pip install -r requirements.txt")

    print("\n2. Run the application:")
    print("   python run_app.py")

    print("\n3. Open in browser:")
    print("   http://localhost:5000")

    print("\n📖 Documentation:")
    print("   QUICKSTART.md - Quick start guide")
    print("   README.md - Full documentation")

    print("\n" + "=" * 70)

except Exception as e:
    print(f"\n✗ ERROR during extraction: {e}")
    print("\nPlease extract the archive manually:")
    if archive_path.suffix == '.gz':
        print(f"  tar -xzf {archive_path.name}")
    else:
        print(f"  unzip {archive_path.name}")

input("\nPress Enter to exit...")