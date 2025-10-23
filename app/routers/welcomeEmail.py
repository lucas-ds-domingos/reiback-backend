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
            <body>
                <p>Olá, <b>{payload.nome}</b>!</p>
                <p>Seu cadastro na Finance Assurance foi realizado com sucesso.</p>
                <p>Você pode acessar seu painel com este e-mail e a senha cadastrada.</p>
                <p>Email: {payload.email}<br></p>
                <p>Senha:(A senha que digitou no cadastro)</p>
                <p>Clique em login</p>
                <p>Acesse o painel: <a href='https://financeassurance.up.railway.app/login'>Login</a></p>
               
            </body>
        </html>
        """
        enviar_email(para=payload.email, assunto="Bem-vindo à Finance Assurance", corpo=corpo_html)
        return {"message": "E-mail enviado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {e}")
