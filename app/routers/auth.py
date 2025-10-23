from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
from ..utils.email import enviar_email
from datetime import datetime, timedelta
import jwt
import os

router = APIRouter()

# Chave secreta (ideal usar .env)
SECRET_KEY = os.getenv("SECRET_KEY", "minha_chave_super_secreta")
ALGORITHM = "HS256"

@router.post("/auth/forgot-password")
def forgot_password(email: str, db: Session = Depends(get_db)):
    # 1️⃣ Verifica se o usuário existe
    user = db.query(Usuario).filter(Usuario.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # 2️⃣ Gera token JWT de redefinição com validade de 1 hora
    token_data = {
        "sub": str(user.id),
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)

    # 3️⃣ Monta o link de redefinição apontando para o front
    frontend_url = os.getenv("FRONTEND_URL", "https://financeassurance.up.railway.app/reset-password")
    link_redefinicao = f"{frontend_url}?token={token}"

    # 4️⃣ Monta o corpo HTML do e-mail
    assunto = "Redefinição de senha - Finance Assurance"
    corpo_html = f"""
    <div style="font-family: Arial; padding: 20px; color: #333;">
        <h2>Olá, {user.nome}!</h2>
        <p>Recebemos uma solicitação para redefinir sua senha.</p>
        <p>Clique no botão abaixo para criar uma nova senha (válido por 1 hora):</p>
        <p>
            <a href="{link_redefinicao}" 
               style="background-color: #004aad; color: white; padding: 10px 20px;
                      text-decoration: none; border-radius: 5px;">
               Redefinir Senha
            </a>
        </p>
        <p style="margin-top: 20px; font-size: 12px; color: #777;">
            Se você não solicitou, ignore este e-mail.
        </p>
    </div>
    """

    # 5️⃣ Envia o e-mail
    try:
        enviar_email(para=email, assunto=assunto, corpo=corpo_html)
        return {"message": "E-mail de redefinição enviado com sucesso"}
    except Exception as e:
        print("Erro ao enviar e-mail:", e)
        raise HTTPException(status_code=500, detail="Erro ao enviar o e-mail")
