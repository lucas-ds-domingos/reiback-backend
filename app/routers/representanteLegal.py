from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import RepresentanteLegal
from schemas.representante_legal import (
    RepresentanteLegalCreate,
    RepresentanteLegalUpdate,
    RepresentanteLegalResponse
)

router = APIRouter(prefix="/representante", tags=["Representantes Legais"])


# 🟢 Criar representante
@router.post("/create", response_model=RepresentanteLegalResponse)
def criar_representante(data: RepresentanteLegalCreate, db: Session = Depends(get_db)):
    novo = RepresentanteLegal(**data.dict())
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


# 🟡 Editar representante
@router.put("/update/{id}", response_model=RepresentanteLegalResponse)
def atualizar_representante(id: int, data: RepresentanteLegalUpdate, db: Session = Depends(get_db)):
    representante = db.query(RepresentanteLegal).filter(RepresentanteLegal.id == id).first()

    if not representante:
        raise HTTPException(status_code=404, detail="Representante não encontrado")

    for key, value in data.dict(exclude_unset=True).items():
        setattr(representante, key, value)

    db.commit()
    db.refresh(representante)
    return representante


# 🔵 Listar representantes de um tomador
@router.get("/list/{tomador_id}", response_model=List[RepresentanteLegalResponse])
def listar_representantes_por_tomador(tomador_id: int, db: Session = Depends(get_db)):
    representantes = db.query(RepresentanteLegal).filter(RepresentanteLegal.tomador_id == tomador_id).all()

    if not representantes:
        raise HTTPException(status_code=404, detail="Nenhum representante encontrado para este tomador")

    return representantes
