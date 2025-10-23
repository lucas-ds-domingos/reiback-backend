import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

def enviar_email(para: str, assunto: str, corpo: str):
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    remetente = os.getenv("EMAIL_FROM")

    msg = MIMEMultipart()
    msg["From"] = remetente
    msg["To"] = para
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "html"))

    try:
        with smtplib.SMTP(host, port) as server:
            server.starttls()
            server.login(user, password)
            server.send_message(msg)
        print("✅ Email enviado")
    except Exception as e:
        print("❌ Erro ao enviar e-mail:", e)
