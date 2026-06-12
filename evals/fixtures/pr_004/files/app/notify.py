import aiosmtplib


async def send(to: str, subject: str, body: str) -> None:
    await aiosmtplib.send(message=body, recipients=[to], subject=subject)


async def notify_user(user_email: str, message: str) -> None:
    send(user_email, "Notification", message)
