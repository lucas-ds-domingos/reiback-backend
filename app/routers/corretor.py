from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Corretora, Usuario, Assessoria, ResponsavelFinanceiroCorretora
from ..schemas.corretor import CorretoraCreate, CorretoraUpdate
from passlib.hash import bcrypt
from datetime import datetime
from decimal import Decimal
from ..utils.get_current_user import get_current_user

router = APIRouter()

@router.post("/corretores")
def criar_corretor(
    payload: CorretoraCreate,
    db: Session = Depends(get_db),
    assessoria_id: int | None = Query(default=None)
):
    """
    Cria uma corretora e um usuário corretor vinculado.
    - Se 'assessoria_id' for passado, a corretora não terá finance_id
      e o usuário será vinculado a essa assessoria.
    - Caso contrário, a corretora terá finance_id=1 e usuário não terá assessoria.
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

    # Dados da corretora
    corretora_data = dict(
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
        data_registro=datetime.utcnow()
    )

    # Só define finance_id se não houver assessoria_id
    if not assessoria_id:
        corretora_data["finance_id"] = 1

    nova_corretora = Corretora(**corretora_data)
    db.add(nova_corretora)
    db.commit()
    db.refresh(nova_corretora)

    # Criptografa a senha do usuário
    hashed_password = bcrypt.hash(payload.password)

    # Verifica se assessoria_id existe
    if assessoria_id:
        assessoria_existente = db.query(Assessoria).filter(Assessoria.id == assessoria_id).first()
        if not assessoria_existente:
            raise HTTPException(status_code=400, detail="Assessoria não encontrada.")

    # Cria o usuário vinculado à corretora e, se houver, à assessoria
    novo_usuario = Usuario(
        nome=payload.razao_social,
        email=payload.email,
        senha_hash=hashed_password,
        role="corretor",
        ativo=True,
        corretora_id=nova_corretora.id,
        criado_em=datetime.utcnow(),
        assessoria_id=assessoria_id 
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "corretora": {
            "id": nova_corretora.id,
            "cnpj": nova_corretora.cnpj,
            "razao_social": nova_corretora.razao_social,
            "finance_id": getattr(nova_corretora, "finance_id", None)
        },
        "usuario": {
            "id": novo_usuario.id,
            "nome": novo_usuario.nome,
            "email": novo_usuario.email,
            "role": novo_usuario.role,
            "assessoria_id": novo_usuario.assessoria_id
        }
    }

@router.put("/corretora")
def update_corretora(
    payload: CorretoraUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Atualiza os dados da corretora do usuário logado, incluindo dados bancários.
    """
    if not current_user.corretora_id:
        raise HTTPException(status_code=404, detail="Usuário não possui corretora vinculada")

    corretora = db.query(Corretora).filter(Corretora.id == current_user.corretora_id).first()
    if not corretora:
        raise HTTPException(status_code=404, detail="Corretora não encontrada")

    # Atualiza campos básicos
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(corretora, field, value)

    db.commit()
    db.refresh(corretora)

    return {"message": "Corretora atualizada com sucesso", "corretora": corretora}

@router.put("/corretora/responsavel")
def update_responsavel(
    nome: str,
    cpf: str,
    email: str,
    telefone: str | None = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Cria ou atualiza o responsável financeiro da corretora do usuário logado.
    """
    if not current_user.corretora_id:
        raise HTTPException(status_code=404, detail="Usuário não possui corretora vinculada")

    corretora = db.query(Corretora).filter(Corretora.id == current_user.corretora_id).first()
    if not corretora:
        raise HTTPException(status_code=404, detail="Corretora não encontrada")

    responsavel = db.query(ResponsavelFinanceiroCorretora).filter(
        ResponsavelFinanceiroCorretora.corretora_id == corretora.id
    ).first()

    if responsavel:
        # Atualiza
        responsavel.nome = nome
        responsavel.cpf = cpf
        responsavel.email = email
        responsavel.telefone = telefone
    else:
        # Cria
        responsavel = ResponsavelFinanceiroCorretora(
            corretora_id=corretora.id,
            nome=nome,
            cpf=cpf,
            email=email,
            telefone=telefone
        )
        db.add(responsavel)

    db.commit()
    db.refresh(responsavel)

    return {"message": "Responsável financeiro atualizado com sucesso", "responsavel": responsavel}