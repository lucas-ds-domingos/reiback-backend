from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Fiador
from ..schemas.fiador import FiadorCreate, FiadorUpdate, FiadorResponse

router = APIRouter(prefix="/fiador", tags=["Fiadores"])

# Criar fiador
@router.post("/create", response_model=FiadorResponse)
def criar_fiador(data: FiadorCreate, db: Session = Depends(get_db)):
    novo = Fiador(**data.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

# Editar fiador
@router.put("/update/{id}", response_model=FiadorResponse)
def atualizar_fiador(id: int, data: FiadorUpdate, db: Session = Depends(get_db)):
    fiador = db.query(Fiador).filter(Fiador.id == id).first()
    if not fiador:
        raise HTTPException(status_code=404, detail="Fiador não encontrado")
    for key, value in data.dict(exclude_unset=True).items():
        setattr(fiador, key, value)
    db.commit()
    db.refresh(fiador)
    return fiador

# Listar fiadores de um tomador
@router.get("/list/{tomador_id}", response_model=List[FiadorResponse])
def listar_fiadores_por_tomador(tomador_id: int, db: Session = Depends(get_db)):
    fiadores = db.query(Fiador).filter(Fiador.tomador_id == tomador_id).all()
    if not fiadores:
        return []
    return fiadores

# Excluir fiador
@router.delete("/delete/{id}")
def deletar_fiador(id: int, db: Session = Depends(get_db)):
    fiador = db.query(Fiador).filter(Fiador.id == id).first()
    if not fiador:
        raise HTTPException(status_code=404, detail="Fiador não encontrado")
    db.delete(fiador)
    db.commit()
    return {"detail": "Fiador deletado com sucesso"}
