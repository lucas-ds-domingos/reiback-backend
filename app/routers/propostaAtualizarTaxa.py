from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import date
from ..database import get_db
from ..models import Proposta
from ..schemas.proposta  import PropostaResponse
router = APIRouter()

@router.patch("/propostas/{proposta_id}/atualizar-taxa", response_model=PropostaResponse)
def atualizar_taxa(
    proposta_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):
    nova_taxa = Decimal(str(payload.get("taxa_percentual")))
    if nova_taxa <= 0:
        raise HTTPException(status_code=400, detail="Taxa inválida")

    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    if not proposta.importancia_segurada or not proposta.dias_vigencia:
        raise HTTPException(status_code=400, detail="Proposta sem dados de cálculo")

    # === Recalcular prêmio ===
    importancia = proposta.importancia_segurada
    dias = max(proposta.dias_vigencia, 90) 
    taxa_decimal = nova_taxa / Decimal("100")
    premio = ((importancia * taxa_decimal) / Decimal("365")) * dias
    premio = max(premio, Decimal("250")) 

    # === Comissão ===
    comissao_percent = proposta.comissao_percentual or Decimal("20.00")
    comissao_valor = (premio * comissao_percent) / Decimal("100")

    # === Atualizar ===
    proposta.taxa_percentual = nova_taxa
    proposta.premio = premio
    proposta.comissao_valor = comissao_valor

    db.commit()
    db.refresh(proposta)
    return proposta
