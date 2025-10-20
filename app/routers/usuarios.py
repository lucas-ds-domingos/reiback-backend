from fastapi import APIRouter, HTTPException, Depends,status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario, Corretora
from ..utils.auts import hash_password, verify_password, create_access_token
from ..schemas.usuarios import UsuarioCreate, LoginSchema, UsuarioCreateFisico, UsuarioResponse, UsuarioUpdate
from ..utils.get_current_user import get_current_user
from typing import List


router = APIRouter()

@router.post("/usuarios")
def criar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    # verifica se usuário já existe
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_password(usuario.senha)
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {"id": novo_usuario.id, "nome": novo_usuario.nome, "email": novo_usuario.email}

@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.email == data.email).first()
    if not usuario or not verify_password(data.senha, usuario.senha_hash):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")

    token = create_access_token({"usuario_id": usuario.id})
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {"id": usuario.id, "nome": usuario.nome, "email": usuario.email, "role": usuario.role},
    }

@router.get("/me")
def get_me(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    """
    Retorna os dados do usuário logado, incluindo a corretora vinculada
    """
    if not current_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    corretora = None
    if current_user.corretora_id:
        corretora = db.query(Corretora).filter(Corretora.id == current_user.corretora_id).first()
    
    return {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "role": current_user.role,
        "corretora": {
            "id": corretora.id,
            "nome": corretora.razao_social,
            "cnpj": corretora.cnpj,
            "email": current_user.email,
            "telefone": corretora.telefone,
            "endereco": corretora.endereco,
            "cidade": corretora.cidade,
            "uf": corretora.uf,
            "cep": corretora.cep,
            "numero": corretora.numero,
            "complemento": corretora.complemento,
            "bairro": corretora.bairro,
            "susep": corretora.susep,
            # dados bancários
            "banco": corretora.banco,
            "tipo_conta": corretora.tipo_conta,
            "agencia": corretora.agencia,
            "digito_agencia": corretora.digito_agencia,
            "conta": corretora.conta,
            "digito_conta": corretora.digito_conta,
            "pix": corretora.pix ,
            # responsável financeiro
            "responsavel": {
                "nome": corretora.responsavel.nome,
                "cpf": corretora.responsavel.cpf,
                "email": corretora.responsavel.email,
                "telefone": corretora.responsavel.telefone
            } if corretora.responsavel else None
        } if corretora else None
    }

@router.post("/usuarios-fisico")
def criar_usuario_pf(
    usuario_data: UsuarioCreateFisico,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)  # Token do usuário logado
):
    # Verificar se o email já existe
    if db.query(Usuario).filter(Usuario.email == usuario_data.email).first():
        raise HTTPException(status_code=400, detail="Usuário já existe")

    # Preparar vínculos com base no usuário logado
    corretora_id = None
    assessoria_id = None
    finance_id = None

    if current_user.role == "corretor":
        corretora_id = current_user.corretora_id  # Vincula à mesma corretora
    elif current_user.role == "assessoria":
        assessoria_id = current_user.assessoria_id  # Vincula à mesma assessoria
    elif current_user.role == "master":
        finance_id = current_user.finance_id  # Vincula ao financeiro

    # Criar o novo usuário PF
    novo_usuario = Usuario(
        nome=usuario_data.nome,
        email=usuario_data.email,
        senha_hash=hash_password(usuario_data.senha),
        cpf=usuario_data.cpf,
        role="corretor",  # Usuário PF sempre entra como corretor
        corretora_id=corretora_id,
        assessoria_id=assessoria_id,
        finance_id=finance_id
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "id": novo_usuario.id,
        "nome": novo_usuario.nome,
        "email": novo_usuario.email,
        "role": novo_usuario.role,
        "corretora_id": novo_usuario.corretora_id,
        "assessoria_id": novo_usuario.assessoria_id,
        "finance_id": novo_usuario.finance_id
    }


# LISTAR usuários adicionais do usuário logado
@router.get("/meu", response_model=List[UsuarioResponse])
def listar_usuarios_adicionais(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    query = db.query(Usuario)

    if current_user.role == "corretor":
        query = query.filter(Usuario.corretora_id == current_user.id)
    elif current_user.role == "assessoria":
        query = query.filter(Usuario.assessoria_id == current_user.id)
    elif current_user.role == "master":
        pass  # master vê todos

    usuarios = query.all()
    return usuarios


# EDITAR parcialmente
@router.patch("/meu/{usuario_id}", response_model=UsuarioResponse)
def editar_usuario(usuario_id: int, payload: UsuarioUpdate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # valida permissões
    if current_user.role == "corretor" and usuario.corretora_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if current_user.role == "assessoria" and usuario.assessoria_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    # master pode editar qualquer usuário

    for key, value in payload.dict(exclude_unset=True).items():
        setattr(usuario, key, value)

    db.commit()
    db.refresh(usuario)
    return usuario


# DELETAR usuário
@router.delete("/meu/{usuario_id}", status_code=204)
def deletar_usuario(usuario_id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # valida permissões
    if current_user.role == "corretor" and usuario.corretora_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")
    if current_user.role == "assessoria" and usuario.assessoria_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    db.delete(usuario)
    db.commit()
    return