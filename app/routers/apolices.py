from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Apolice, Proposta, Usuario
from ..utils import get_current_user
from pydantic import BaseModel
from datetime import date
from decimal import Decimal
from typing import List

router = APIRouter(
    prefix="/apolices",
    tags=["Apolices"]
)

# Schemas
class PropostaInfo(BaseModel):
    numero: str
    inicio_vigencia: date | None
    termino_vigencia: date | None
    premio: Decimal | None
    tomador_nome: str

class ApoliceResponse(BaseModel):
    id: int
    numero: str
    data_criacao: date
    proposta: PropostaInfo

    class Config:
        orm_mode = True

# Listagem com controle por role
from ..utils.get_current_user import get_current_user
from ..models import Usuario

@router.get("/", response_model=list[ApoliceResponse])
def listar_apolices(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # current_user já é o objeto Usuario, então acessa direto:
    usuario = current_user

    if usuario.role == "master":
        apolices = db.query(Apolice).options(
            joinedload(Apolice.proposta).joinedload(Proposta.tomador)
        ).all()
    elif usuario.role == "assessoria":
        apolices = (
            db.query(Apolice)
            .join(Proposta, Apolice.proposta_id == Proposta.id)
            .join(Usuario, Proposta.usuario_id == Usuario.id)
            .filter(Usuario.assessoria_id == usuario.assessoria_id)
            .options(joinedload(Apolice.proposta).joinedload(Proposta.tomador))
            .all()
        )
    else:  # corretor
        apolices = (
            db.query(Apolice)
            .join(Proposta, Apolice.proposta_id == Proposta.id)
            .filter(Proposta.usuario_id == usuario.id)
            .options(joinedload(Apolice.proposta).joinedload(Proposta.tomador))
            .all()
        )

    result = []
    for a in apolices:
        proposta = a.proposta
        tomador_nome = proposta.tomador.nome if proposta.tomador else "Sem tomador"
        proposta_info = PropostaInfo(
            numero=proposta.numero,
            inicio_vigencia=proposta.inicio_vigencia,
            termino_vigencia=proposta.termino_vigencia,
            premio=proposta.premio,
            tomador_nome=tomador_nome
        )
        result.append(ApoliceResponse(
            id=a.id,
            numero=a.numero,
            data_criacao=a.data_criacao,
            proposta=proposta_info
        ))
    return result
