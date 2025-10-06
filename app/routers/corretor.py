from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from schemas.corretor import CorretoraCreate, CorretoraResponse
from services.corretora_service import create_corretora

router = APIRouter(prefix="/corretoras", tags=["Corretoras"])

@router.post("/", response_model=CorretoraResponse)
def cadastrar_corretora(payload: CorretoraCreate, db: Session = Depends(get_db)):
    try:
        return create_corretora(db, payload)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=400, detail="Erro ao cadastrar corretora"
        )
