from email_service.email_client import EmailClient

print("Running test email...")

client = EmailClient()
client.send_email(
    to="your_test_email@company.com",
    subject="Email Service Test",
    body="This is a test email from your reusable module."
)

print("Test complete.")
