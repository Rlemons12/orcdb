import os
from pathlib import Path
from dotenv import load_dotenv
from email_service.log.email_logger import logger

ENV_PATH = Path.cwd() / "email_service_env"


class EmailConfig:
    """
    Loads configuration from email_service_env.
    Correctly respects EMAIL_MODE so Outlook-only mode does NOT
    require any SMTP fields.
    """

    def __init__(self):
        # Load environment file
        if ENV_PATH.exists():
            load_dotenv(ENV_PATH)
            logger.info(f"Loaded env from {ENV_PATH}")
        else:
            logger.warning(f"No env file found at {ENV_PATH}")

        # Read email mode
        self.email_mode = os.getenv("EMAIL_MODE", "auto").lower()

        # Only load SMTP fields if they may be needed
        if self.email_mode in ("smtp", "auto"):
            self.smtp_server = os.getenv("OUTLOOK_SMTP_SERVER")
            self.smtp_port = int(os.getenv("OUTLOOK_SMTP_PORT", 587))
            self.email = os.getenv("OUTLOOK_EMAIL_ADDRESS")
            self.password = os.getenv("OUTLOOK_EMAIL_PASSWORD")
            self.use_tls = os.getenv("OUTLOOK_USE_TLS", "true").lower() == "true"
        else:
            # Outlook-only mode → skip SMTP
            self.smtp_server = None
            self.smtp_port = None
            self.email = None
            self.password = None
            self.use_tls = None

    # -------------------------------------------------------------
    # Validation ONLY required when SMTP may be used
    # -------------------------------------------------------------
    def validate(self):
        if self.email_mode == "outlook":
            logger.info("Outlook mode selected — skipping SMTP validation.")
            return True

        # SMTP or Auto mode → validate necessary fields
        missing = []
        if not self.smtp_server: missing.append("OUTLOOK_SMTP_SERVER")
        if not self.email: missing.append("OUTLOOK_EMAIL_ADDRESS")
        if not self.password: missing.append("OUTLOOK_EMAIL_PASSWORD")

        if missing:
            logger.error(f"Missing required SMTP fields: {', '.join(missing)}")
            return False

        return True
