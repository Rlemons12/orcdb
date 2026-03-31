# email_service/smtp_sender.py

import smtplib
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from email_service.config.email_config import EmailConfig
from email_service.log.email_logger import logger


class SMTPSender:
    """Handles sending email through SMTP."""

    def __init__(self):
        self.config = EmailConfig()
        if not self.config.validate():
            raise ValueError("SMTP configuration is invalid.")

    def send(self, to, subject, body, attachments=None, html=False, cc=None, bcc=None):
        if isinstance(to, str):
            to = [to]
        cc = cc or []
        bcc = bcc or []

        msg = MIMEMultipart()
        msg["From"] = self.config.email
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "html" if html else "plain"))

        # Attachments
        if attachments:
            for file in attachments:
                fp = Path(file)
                if fp.exists():
                    with open(fp, "rb") as f:
                        part = MIMEApplication(f.read(), Name=fp.name)
                    part["Content-Disposition"] = f'attachment; filename="{fp.name}"'
                    msg.attach(part)
                    logger.info(f"Attached: {fp}")
                else:
                    logger.warning(f"Attachment not found: {fp}")

        try:
            logger.info("Connecting to SMTP server...")

            server = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)
            if self.config.use_tls:
                server.starttls()

            server.login(self.config.email, self.config.password)
            server.sendmail(self.config.email, to + cc + bcc, msg.as_string())
            server.quit()

            logger.info(f"SMTP email successfully sent to: {to}")

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            raise
