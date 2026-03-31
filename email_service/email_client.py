# email_service/email_client.py

from email_service.outlook_sender import OutlookSender
from email_service.smtp_sender import SMTPSender
from email_service.log.email_logger import logger
from email_service.config.email_config import EmailConfig


class EmailClient:
    """
    Unified email engine:
        - Outlook mode (never uses SMTP)
        - SMTP mode (never uses Outlook)
        - Auto mode (Outlook → fallback → SMTP)
    """

    def __init__(self, preferred="auto"):
        config = EmailConfig()
        self.mode = config.__dict__.get("email_mode", preferred)

        self.outlook = OutlookSender()
        self.smtp = SMTPSender()

        # Normalize
        if self.mode not in ("outlook", "smtp", "auto"):
            self.mode = "auto"

        logger.info(f"EmailClient initialized with mode: {self.mode.upper()}")

    # -----------------------------------------------------------
    # Unified sending
    # -----------------------------------------------------------
    def send_email(self, to, subject, body, attachments=None, html=False, cc=None, bcc=None):
        import win32com.client as win32

        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)

        mail.Subject = subject
        mail.HTMLBody = body if html else body

        if isinstance(to, list):
            mail.To = "; ".join(to)
        else:
            mail.To = to

        if cc:
            mail.CC = "; ".join(cc) if isinstance(cc, list) else cc

        if attachments:
            for file_path in attachments:
                mail.Attachments.Add(str(file_path))

        mail.Send()
        return True



