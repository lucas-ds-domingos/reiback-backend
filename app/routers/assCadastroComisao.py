from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal

from ..database import get_db
from ..models import Assessoria
from ..schemas.assesorias import AssesoriaResponse
from pydantic import BaseModel

router = APIRouter()


# ==============================
# Schema para atualizar comissão
# ==============================
class AtualizarComissao(BaseModel):
    comissao: Decimal

# =========================================
# PUT - Atualizar comissão da assessoria
# =========================================
@router.put("/assessorias/{assessoria_id}/comissao", response_model=AssesoriaResponse)
def update_comissao_assessoria(
    assessoria_id: int,
    payload: AtualizarComissao,
    db: Session = Depends(get_db),
):
    assessoria = db.query(Assessoria).filter(Assessoria.id == assessoria_id).first()
    if not assessoria:
        raise HTTPException(status_code=404, detail="Assessoria não encontrada.")

    # validação da comissão
    if payload.comissao < 0 or payload.comissao > 100:
        raise HTTPException(status_code=400, detail="A comissão deve estar entre 0 e 100%.")

    assessoria.comissao = Decimal(payload.comissao)
    db.commit()
    db.refresh(assessoria)

    return assessoria
