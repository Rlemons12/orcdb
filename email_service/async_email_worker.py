import asyncio
from asyncio import Queue
from email_service.email_client import EmailClient
from email_service.log.email_logger import logger

class EmailWorker:
    def __init__(self):
        self.queue = Queue()
        self.client = EmailClient()

    async def worker(self):
        while True:
            job = await self.queue.get()
            try:
                await self.client.send_email_async(**job)
                logger.info("Queued email sent.")
            except Exception as e:
                logger.error(f"Queued email failed: {e}")
            self.queue.task_done()

    async def start(self):
        asyncio.create_task(self.worker())

    async def queue_email(self, to, subject, body, attachments=None, html=False):
        await self.queue.put({
            "to": to,
            "subject": subject,
            "body": body,
            "attachments": attachments,
            "html": html
        })
