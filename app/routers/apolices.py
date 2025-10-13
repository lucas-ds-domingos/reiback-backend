from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session, joinedload
from ..database import get_db
from ..models import Apolice, Proposta, Usuario
from ..utils.get_current_user import get_current_user
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
@router.get("/", response_model=List[ApoliceResponse])
def listar_apolices(
    db: Session = Depends(get_db),
    current_user_data: dict = Depends(get_current_user)  # só vem id
):
    # Busca usuário completo no banco
    usuario = db.query(Usuario).filter(Usuario.id == current_user_data["id"]).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Query base com joinedload
    query = db.query(Apolice).options(
        joinedload(Apolice.proposta).joinedload(Proposta.tomador)
    )

    # Filtro por role
    if usuario.role == "corretor":
        query = query.join(Apolice.proposta).filter(Proposta.usuario_id == usuario.id)
    elif usuario.role == "assessoria":
        # Todas apólices de propostas dos corretores da assessoria
        query = query.join(Apolice.proposta).join(Usuario).filter(Usuario.assessoria_id == usuario.assessoria_id)
    # master vê tudo -> não filtra

    apolices = query.all()

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
