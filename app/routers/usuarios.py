from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Usuario
from ..utils.auts import hash_password, verify_password, create_access_token
from ..schemas.usuarios import UsuarioCreate, LoginSchema

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
