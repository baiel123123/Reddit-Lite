import smtplib
from email.message import EmailMessage

from src.celery_app import celery_app
from src.config.settings import get_email_settings

email_settings = get_email_settings()


@celery_app.task
def send_verification_email(email: str, code: str):
    msg = EmailMessage()
    msg["Subject"] = "Подтверждение регистрации"
    msg["From"] = email_settings["email_from"]
    msg["To"] = email
    msg.set_content(f"Ваш код подтверждения: {code}")

    try:
        with smtplib.SMTP(email_settings["smtp_server"], email_settings["smtp_port"]) as server:
            server.starttls()
            server.login(email_settings["email_from"], email_settings["email_password"])
            server.send_message(msg)
    except Exception as e:
        print(f"Ошибка при отправке email: {e}")
