from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Assessoria, Usuario
from ..schemas.assesorias import AssesoriaCreate, AssesoriaBase
from passlib.hash import bcrypt
from datetime import datetime
from decimal import Decimal
from typing import List
from ..utils.get_current_user import get_current_user

router = APIRouter()

@router.post("/assessoria")
def criar_corretor(payload: AssesoriaCreate, db: Session = Depends(get_db)):
    # Verifica se o CNPJ já existe
    existente = db.query(Assessoria).filter(Assessoria.cnpj == payload.cnpj).first()
    if existente:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")
    # Cria a corretora
    nova_corretora = Assessoria(
        finance_id=1,
        cnpj=payload.cnpj,
        razao_social=payload.razao_social,
        telefone=payload.telefone,
        cep=payload.cep,
        endereco=payload.endereco,
        numero=payload.numero,
        complemento=payload.complemento,
        bairro=payload.bairro,
        uf=payload.uf,
        cidade=payload.cidade,
        data_registro=datetime.utcnow(),
    )
    db.add(nova_corretora)
    db.commit()
    db.refresh(nova_corretora)

    # Criptografa a senha do usuário
    hashed_password = bcrypt.hash(payload.password)

    # Cria o usuário vinculado à corretora
    novo_usuario = Usuario(
        nome=payload.razao_social,
        email=payload.email,
        senha_hash=hashed_password,
        role="assessoria",
        ativo=True,
        assessoria_id=nova_corretora.id,
        criado_em=datetime.utcnow()
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "corretora": {
            "id": nova_corretora.id,
            "cnpj": nova_corretora.cnpj,
            "razao_social": nova_corretora.razao_social
        },
        "usuario": {
            "id": novo_usuario.id,
            "nome": novo_usuario.nome,
            "email": novo_usuario.email,
            "role": novo_usuario.role
        }
    }



@router.get("/list-assesoria", response_model=List[AssesoriaBase])
def listar_assessorias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Se for MASTER → vê tudo
    if current_user.role == "master":
        assessorais = db.query(Assessoria).all()

    # Se for ASSESSORIA → vê somente a própria
    elif current_user.role == "assessoria":
        assessorais = db.query(Assessoria).filter(
            Assessoria.id == current_user.assessoria_id
        ).all()

    # Se for CORRETOR ou outro → não vê nada (ou pode retornar apenas a própria assessoria dele, se quiser)
    else:
        assessorais = []

    return assessorais
