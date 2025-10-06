from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Corretora
from ..schemas.corretor import CorretoraCreate, CorretoraResponse
from passlib.hash import bcrypt

router = APIRouter()

@router.post("/corretores", response_model=CorretoraResponse)
def criar_corretor(payload: CorretoraCreate, db: Session = Depends(get_db)):
    # Verifica se o CNPJ já existe
    corretor_existente = db.query(Corretora).filter(Corretora.cnpj == payload.cnpj).first()
    if corretor_existente:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    # Criptografa a senha antes de salvar
    hashed_password = bcrypt.hash(payload.password)

    novo_corretor = Corretora(
        cnpj=payload.cnpj,
        razao_social=payload.razao_social,
        inscricao_municipal=payload.inscricao_municipal,
        telefone=payload.telefone,
        cep=payload.cep,
        endereco=payload.endereco,
        numero=payload.numero,
        complemento=payload.complemento,
        bairro=payload.bairro,
        uf=payload.uf,
        cidade=payload.cidade,
        comissao=payload.comissao or 0,
        email=payload.email,
        password=hashed_password,
        susep=payload.susep or None, 
    )

    db.add(novo_corretor)
    db.commit()
    db.refresh(novo_corretor)

    return novo_corretor
