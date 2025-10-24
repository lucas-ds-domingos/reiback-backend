from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..utils.email import enviar_email

router = APIRouter()

class WelcomeEmailSchema(BaseModel):
    email: str
    nome: str

@router.post("/send-welcome-email")
def send_welcome_email(payload: WelcomeEmailSchema):
    try:
        corpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; color: #333;">
                <h2>Bem-vindo à Finance Assurance!</h2>
                <p>Olá, <b>{payload.nome}</b> 👋</p>
                <p>Seu cadastro foi realizado com sucesso.</p>
                <p>Login é o email de cadastro e a senha a senha que colocou no cadastro</p>
                <p>Agora você pode acessar o painel clicando abaixo:</p>
                <p>
                    <a href="https://financeassurance.up.railway.app/login"
                       style="background-color: #004aad; color: white; 
                              padding: 10px 20px; text-decoration: none; border-radius: 6px;">
                        Acessar Login
                    </a>
                </p>
                <p style="font-size: 12px; color: #777;">
                    Se você não realizou este cadastro, ignore este e-mail.
                </p>
            </body>
        </html>
        """
        enviar_email(
            para=payload.email,
            assunto="Bem-vindo à Finance Assurance",
            corpo=corpo_html
        )
        return {"message": "E-mail enviado com sucesso"}
    except Exception as e:
        print(f"⚠️ Erro ao enviar e-mail: {e}")
        # Não lançar erro 500 pra não quebrar o fluxo de cadastro
        return {"message": "Cadastro realizado, mas o e-mail não pôde ser enviado"}
