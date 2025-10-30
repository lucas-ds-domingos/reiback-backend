import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv
import ssl

load_dotenv()

def enviar_email(para: str, assunto: str, corpo: str):
    host = os.getenv("EMAIL_HOST")
    port = int(os.getenv("EMAIL_PORT"))
    user = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    remetente = os.getenv("EMAIL_FROM").strip()  # remove espaços extras

    # Cria a mensagem
    msg = EmailMessage()
    msg["From"] = remetente
    msg["To"] = para
    msg["Subject"] = assunto
    msg.set_content("Este e-mail precisa ser visto em HTML")  # fallback para texto
    msg.add_alternative(corpo, subtype="html")  # corpo HTML

    try:
        # Cria contexto SSL seguro
        context = ssl.create_default_context()

        # Conecta no servidor SMTP
        with smtplib.SMTP(host, port) as server:
            server.starttls(context=context)  # TLS seguro
            server.login(user, password)
            server.send_message(msg)

        print("✅ Email enviado com sucesso!")
    except Exception as e:
        print("❌ Erro ao enviar e-mail:", e)
