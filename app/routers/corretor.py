from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Corretora, Usuario
from ..schemas.corretor import CorretoraCreate
from passlib.hash import bcrypt
from datetime import datetime
from decimal import Decimal

router = APIRouter()

@router.post("/corretores")
def criar_corretor(
    payload: CorretoraCreate,
    db: Session = Depends(get_db),
    assessoria_id: int | None = Query(default=None)
):
    """
    Cria uma corretora e um usuário corretor vinculado.
    Se 'assessoria_id' vier via query string (?assessoria_id=1),
    o usuário será vinculado àquela assessoria.
    Caso contrário, será uma corretora vinculada à finance_id padrão (1).
    """

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
        finance_id=1  # mantém o padrão
    )

    db.add(nova_corretora)
    db.commit()
    db.refresh(nova_corretora)

    # Criptografa a senha do usuário
    hashed_password = bcrypt.hash(payload.password)

    # Cria o usuário vinculado à corretora e (opcionalmente) à assessoria
    novo_usuario = Usuario(
        nome=payload.razao_social,
        email=payload.email,
        senha_hash=hashed_password,
        role="corretor",
        ativo=True,
        corretora_id=nova_corretora.id,
        criado_em=datetime.utcnow(),
        assessoria_id=assessoria_id  # <-- vincula o usuário à assessoria recebida
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
            "role": novo_usuario.role,
            "assessoria_id": novo_usuario.assessoria_id
        }
    }
