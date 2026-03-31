import win32com.client as win32


def send_email_via_outlook(to, subject, body):
    outlook = win32.Dispatch('outlook.application')
    mail = outlook.CreateItem(0)  # 0 = standard mail item
    mail.To = to
    mail.Subject = subject
    mail.Body = body
    mail.Send()
    print("Email sent via Outlook Desktop!")


if __name__ == "__main__":
    send_email_via_outlook(
        to="robert.lemons@icumed.com",
        subject="Outlook Desktop Test",
        body="This email was sent using the Outlook desktop app."
    )
