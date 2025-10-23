from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets

from ..database import get_db
from ..models import Usuario, PasswordReset
from ..schemas.password_reset import PasswordResetRequest, PasswordResetCreate, PasswordResetResponse
from ..utils.auts import hash_password
from ..utils.email import enviar_email

router = APIRouter()

# =========================
# 🔹 Solicitar link de redefinição
# =========================
@router.post("/password/forgot", response_model=PasswordResetResponse)
def forgot_password(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == payload.email).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Email não encontrado")

    # Remove tokens anteriores do mesmo usuário
    db.query(PasswordReset).filter(PasswordReset.user_id == usuario.id).delete()
    db.commit()

    # Cria token único e define expiração (15 min)
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=15)

    # Salva novo token no banco
    reset = PasswordReset(user_id=usuario.id, token=token, expires_at=expires_at)
    db.add(reset)
    db.commit()
    db.refresh(reset)

    # Link de redefinição para o frontend
    frontend_url = "https://financeassurance.up.railway.app/reset-password"
    link = f"{frontend_url}?token={token}"

    # Corpo do e-mail
    corpo_email = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <p>Olá, <b>{usuario.nome}</b>!</p>
            <p>Recebemos uma solicitação para redefinir sua senha.</p>
            <p>Clique no botão abaixo para criar uma nova senha (válido por 15 minutos):</p>
            <p>
                <a href="{link}" 
                   style="background-color: #004aad; color: white; padding: 10px 20px;
                          text-decoration: none; border-radius: 6px;">
                   Redefinir Senha
                </a>
            </p>
            <p style="font-size: 12px; color: #777;">
                Se você não solicitou, ignore este e-mail.
            </p>
        </body>
    </html>
    """

    # Envia o e-mail
    enviar_email(
        para=usuario.email,
        assunto="Redefinição de senha - Finance Assurance",
        corpo=corpo_email
    )

    return {"message": "Link de recuperação enviado para seu email."}

# =========================
# 🔹 Redefinir senha
# =========================
@router.post("/password/reset", response_model=PasswordResetResponse)
def reset_password(payload: PasswordResetCreate, db: Session = Depends(get_db)):
    reset = db.query(PasswordReset).filter(PasswordReset.token == payload.token).first()
    if not reset:
        raise HTTPException(status_code=400, detail="Token inválido")

    if reset.expires_at < datetime.utcnow():
        db.delete(reset)
        db.commit()
        raise HTTPException(status_code=400, detail="Token expirado")

    usuario = db.query(Usuario).filter(Usuario.id == reset.user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Atualiza a senha
    usuario.senha = hash_password(payload.nova_senha)
    db.add(usuario)

    # Remove o token usado
    db.delete(reset)
    db.commit()

    return {"message": "Senha redefinida com sucesso!"}
