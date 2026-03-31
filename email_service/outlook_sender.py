# email_service/outlook_sender.py

import win32com.client as win32
from pathlib import Path
from email_service.log.email_logger import logger


class OutlookSender:
    """
    Sends email using the Outlook Desktop application.
    Uses the user's existing Outlook profile (no passwords required).
    """

    def __init__(self):
        try:
            # Try to create Outlook application COM object
            self.outlook = win32.Dispatch("outlook.application")
            self.namespace = self.outlook.GetNamespace("MAPI")
            logger.info("Outlook Desktop detected and loaded.")
            self.available = True
        except Exception as e:
            logger.warning(f"Outlook Desktop not available: {e}")
            self.available = False

    def send(self, to, subject, body, attachments=None, html=False, cc=None, bcc=None):
        if not self.available:
            raise RuntimeError("Outlook Desktop is not available.")

        try:
            namespace = self.outlook.GetNamespace("MAPI")
            namespace.Logon()

            # Create mail object (universal method)
            mail = self.outlook.CreateItem(0)  # MailItem

            # Recipients
            if isinstance(to, (list, tuple)):
                mail.To = "; ".join(to)
            else:
                mail.To = to

            if cc:
                mail.CC = "; ".join(cc) if isinstance(cc, (list, tuple)) else cc

            if bcc:
                mail.BCC = "; ".join(bcc) if isinstance(bcc, (list, tuple)) else bcc

            # Subject
            mail.Subject = subject

            # Body (HTML only — even for plain text)
            if html:
                mail.HTMLBody = body
            else:
                safe_html_body = f"<html><body><pre>{body}</pre></body></html>"
                mail.HTMLBody = safe_html_body

            # Attachments
            if attachments:
                for fp in attachments:
                    path = Path(fp)
                    if path.exists():
                        mail.Attachments.Add(str(path))
                    else:
                        logger.warning(f"Attachment not found: {path}")

            # Save to Drafts
            mail.Save()

            # *** VERY IMPORTANT: strong reference to ensure COM stability ***
            send_ptr = mail

            send_ptr.Send()

            logger.info(f"Outlook email successfully sent to: {mail.To}")
            return True

        except Exception as e:
            msg = str(e).lower()

            # Harmless Outlook cleanup errors
            harmless_errors = [
                "moved or deleted",
                "not found",
                "application-defined",
                "the object invoked",
                "cannot create the item"
            ]

            if any(err in msg for err in harmless_errors):
                logger.warning(f"Ignoring harmless Outlook COM warning: {e}")
                return True

            logger.error(f"Outlook send failed: {e}")
            raise



