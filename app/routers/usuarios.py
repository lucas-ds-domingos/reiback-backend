from fastapi import APIRouter, HTTPException, Depends,status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario, Corretora
from ..utils.auts import hash_password, verify_password, create_access_token
from ..schemas.usuarios import UsuarioCreate, LoginSchema, UsuarioCreateFisico
from ..utils.get_current_user import get_current_user


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
def criar_usuario(usuario: UsuarioCreateFisico, db: Session = Depends(get_db)):
    usuario_existente = db.query(Usuario).filter(Usuario.email == usuario.email).first()
    if usuario_existente:
        raise HTTPException(status_code=400, detail="Usuário já existe")

    novo_usuario = Usuario(
        nome=usuario.nome,
        email=usuario.email,
        senha_hash=hash_password(usuario.senha),
        cpf= usuario.cpf
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {"id": novo_usuario.id, "nome": novo_usuario.nome, "email": novo_usuario.email}