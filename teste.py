from app.utils.email import enviar_email


enviar_email(
    para="lukinhascraftman@gmail.com",
    assunto="Teste MailerSend",
    corpo="<h1>Deu certo! 🚀</h1><p>Envio funcionando com MailerSend SMTP.</p>"
)