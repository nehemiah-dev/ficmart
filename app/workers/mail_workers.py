from app.workers.celery import celery
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType
from app.config import settings
import asyncio
from app.workers.templates import welcome_template, order_template
from dotenv import load_dotenv

load_dotenv()

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_username,
    MAIL_PORT=465,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_FROM_NAME="Ficmart",
    MAIL_SSL_TLS=True,
    MAIL_STARTTLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
)


@celery.task
def send_signup_mail(email):
    message = MessageSchema(
        subject="Welcome to Ficmart",
        recipients=[email],
        body=welcome_template,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    asyncio.run(fm.send_message(message))

    return {"message": "email has been sent"}


@celery.task
def send_order_mail(email):
    message = MessageSchema(
        subject="Order details from Ficmart",
        recipients=[email],
        body=order_template,
        subtype=MessageType.html,
    )
    fm = FastMail(conf)
    asyncio.run(fm.send_message(message))


@celery.task
def send_reset_email(email, token):

    reset_link = f"http://localhost:8000/reset-password?token={token}"

    html = f"""
    <h2>Password Reset</h2>

    <p>Click the link below to reset your password</p>

    <a href="{reset_link}">Reset Password</a>

    <p>This link expires in 30 minutes.</p>
    """
    message = MessageSchema(
        subject="Ficmart",
        recipients=[email],
        body=html,
        subtype=MessageType.html
    )
    fm = FastMail(conf)
    asyncio.run(fm.send_message(message))