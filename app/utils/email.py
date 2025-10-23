import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from decouple import config

def enviar_email(para: str, assunto: str, corpo: str):
    """
    Envia um e-mail usando o SMTP do seu domínio empresarial.
    corpo: HTML do e-mail
    """
    remetente = config("EMAIL_USER")
    senha = config("EMAIL_PASS")
    host = config("EMAIL_HOST")
    port = config("EMAIL_PORT", cast=int, default=587)

    # Monta a mensagem
    msg = MIMEMultipart("alternative")
    msg["From"] = remetente
    msg["To"] = para
    msg["Subject"] = assunto
    msg.attach(MIMEText(corpo, "html"))

    try:
        if port == 465:  # SSL
            with smtplib.SMTP_SSL(host, port) as server:
                server.login(remetente, senha)
                server.sendmail(remetente, para, msg.as_string())
        else:  # TLS 587
            with smtplib.SMTP(host, port) as server:
                server.starttls()
                server.login(remetente, senha)
                server.sendmail(remetente, para, msg.as_string())

        print(f"✅ Email enviado para {para}")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail: {e}")
