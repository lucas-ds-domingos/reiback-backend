from sqlalchemy.orm import Session, joinedload
from fastapi import APIRouter, Depends,Response, HTTPException
from ..database import get_db
from ..models import Apolice, Proposta



router = APIRouter()


router = APIRouter(
    prefix="/apolices",
    tags=["Apolices"]
)

from pydantic import BaseModel
from datetime import date
from decimal import Decimal

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

@router.get("/", response_model=list[ApoliceResponse])
def listar_apolices(db: Session = Depends(get_db)):
    # Carrega Apolice + Proposta + Tomador de uma vez
    apolices = db.query(Apolice).options(
        joinedload(Apolice.proposta).joinedload(Proposta.tomador)
    ).all()

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



@router.get("/apolice/{apolice_id}/download")
def download_apolice(apolice_id: int, db: Session = Depends(get_db)):
    apolice = db.query(Apolice).filter(Apolice.id == apolice_id).first()
    if not apolice or not apolice.pdf_assinado:
        raise HTTPException(status_code=404, detail="PDF não encontrado")
    
    return Response(
        content=apolice.pdf_assinado,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=Apolice-{apolice.numero}.pdf"}
    )
