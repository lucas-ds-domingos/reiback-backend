from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Corretora, Usuario
from ..schemas.corretor import CorretoraCreate
from passlib.hash import bcrypt
from datetime import datetime
from decimal import Decimal

router = APIRouter()

@router.post("/corretores")
def criar_corretor(payload: CorretoraCreate, db: Session = Depends(get_db)):
    # Verifica se o CNPJ já existe
    existente = db.query(Corretora).filter(Corretora.cnpj == payload.cnpj).first()
    if existente:
        raise HTTPException(status_code=400, detail="CNPJ já cadastrado.")

    # Tratamento de tipos
    try:
        susep = int(payload.susep) if payload.susep else None
        comissao = Decimal(payload.comissao or 0).quantize(Decimal("0.01"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar números: {e}")

    # Cria a corretora
    nova_corretora = Corretora(
        finance_id=1,
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
        susep=susep,
        situacao_cnpj="ativo",
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
        role="corretor",
        ativo=True,
        corretora_id=nova_corretora.id,
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
