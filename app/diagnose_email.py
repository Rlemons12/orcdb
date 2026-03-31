"""
Email Service Diagnostic Tool
Tests your email integration step-by-step
"""

import sys
from pathlib import Path

print("=" * 70)
print("Email Service Diagnostic Tool")
print("=" * 70)
print()

# Test 1: Check if email_service exists
print("[1/6] Checking email_service folder...")
email_service_path = Path.cwd() / "email_service"
if email_service_path.exists():
    print(f"✓ Found: {email_service_path}")
else:
    print(f"✗ NOT FOUND: {email_service_path}")
    print("   Fix: Create email_service folder in project root")
    sys.exit(1)

# Test 2: Check imports
print("\n[2/6] Testing imports...")
try:
    from email_service.email_client import EmailClient
    print("✓ EmailClient imported successfully")
except ImportError as e:
    print(f"✗ Import failed: {e}")
    print("   Fix: Check email_service structure and __init__.py files")
    sys.exit(1)

# Test 3: Check configuration
print("\n[3/6] Checking configuration...")
env_file = Path.cwd() / "email_service_env"
if env_file.exists():
    print(f"✓ Config file found: {env_file}")
    with open(env_file, 'r') as f:
        print("   Contents:")
        for line in f:
            if line.strip() and not line.startswith('#'):
                print(f"   {line.strip()}")
else:
    print(f"✗ Config file NOT FOUND: {env_file}")
    print("   Fix: Create email_service_env file")

# Test 4: Initialize EmailClient
print("\n[4/6] Initializing EmailClient...")
try:
    client = EmailClient()
    print(f"✓ EmailClient initialized")
    print(f"   Mode: {client.mode}")
    print(f"   Outlook available: {client.outlook.available}")
except Exception as e:
    print(f"✗ Initialization failed: {e}")
    sys.exit(1)

# Test 5: Check Outlook
print("\n[5/6] Checking Outlook availability...")
if client.outlook.available:
    print("✓ Outlook is available")
    print("   Will use Outlook to send emails")
else:
    print("⚠ Outlook is NOT available")
    print("   Will try SMTP (if configured)")

# Test 6: Send test email
print("\n[6/6] Sending test email...")
test_email = input("Enter your email address to test: ").strip()

if not test_email:
    print("⚠ Skipping email test")
else:
    try:
        client.send_email(
            to=test_email,
            subject="Test Email from Oracle DB Reporting System",
            body="This is a test email. If you received this, email integration is working!",
            html=False
        )
        print(f"✓ Test email sent to {test_email}")
        print("   Check your inbox (and spam folder)")
    except Exception as e:
        print(f"✗ Email send failed: {e}")
        print("\nError details:")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Diagnostic Complete")
print("=" * 70)
print("\nIf test email failed, check:")
print("1. Outlook is installed and logged in")
print("2. email_service_env is configured correctly")
print("3. SMTP settings are correct (if using SMTP mode)")
print("4. No firewall blocking email")