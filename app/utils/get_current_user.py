from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
import os
from dotenv import load_dotenv

load_dotenv() 
SECRET_KEY = os.getenv("SECRET_KEY")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")
if not SECRET_KEY:
    raise RuntimeError("Variável SECRET_KEY não encontrada no ambiente")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id: int = payload.get("usuario_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    user = db.query(Usuario).filter(Usuario.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    return user
