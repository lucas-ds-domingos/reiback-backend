from app.utils.email import enviar_email

enviar_email(
    para="lukinhascraftman@gmail.com",
    assunto="Teste de envio - Finance Assurance",
    corpo="""
    <h3>Olá!</h3>
    <p>Este é um teste de envio de e-mail usando finance@financeassurance.com.br</p>
    """
)
