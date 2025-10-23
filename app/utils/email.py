import os
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

def enviar_email(para: str, assunto: str, corpo: str):
    try:
        smtp_server = os.getenv("EMAIL_HOST", "smtp.mailersend.net")
        port = int(os.getenv("EMAIL_PORT", 587))
        login = os.getenv("EMAIL_HOST_USER")
        senha = os.getenv("EMAIL_HOST_PASSWORD")
        remetente = os.getenv("EMAIL_FROM", login)

        # Monta o e-mail (HTML + texto alternativo)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = assunto
        msg["From"] = remetente
        msg["To"] = para
        msg.attach(MIMEText(corpo, "html"))

        # Conecta ao servidor e envia
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            server.login(login, senha)
            server.send_message(msg)

        print("✅ Email enviado com sucesso")

    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
