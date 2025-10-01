from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
from ..utils.auts import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")
    
    usuario = db.query(Usuario).filter(Usuario.id == payload.get("usuario_id")).first()
    if not usuario:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return usuario
