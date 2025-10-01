from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta, Apolice
from datetime import datetime
from decimal import Decimal
from .d4sign_tasks import enviar_para_d4sign_e_salvar

router = APIRouter()

@router.post("/webhook-asaas")
def asaas_webhook(payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    event = payload.get("event")
    payment = payload.get("payment", {})

    if event != "PAYMENT_RECEIVED":
        return {"status": "ignored"}

    try:
        proposta_id = int(payment.get("externalReference"))
    except (TypeError, ValueError):
        return {"status": "ignored"}

    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        return {"status": "proposta not found"}

    # Atualiza status da proposta
    proposta.status = "paga"
    proposta.valor_pago = Decimal(str(payment.get("netValue", payment.get("value"))))
    if payment.get("paymentDate"):
        proposta.pago_em = datetime.strptime(payment["paymentDate"], "%Y-%m-%d")
    db.commit()
    db.refresh(proposta)

    # Cria apólice
    apolice = Apolice(
        proposta_id=proposta.id,
        numero=f"FIN-{proposta.id:05d}",
        data_criacao=datetime.utcnow(),
        status_assinatura="pendente"
    )
    db.add(apolice)
    db.commit()
    db.refresh(apolice)

    # Chama função em background para gerar PDF e enviar ao D4Sign
    background_tasks.add_task(enviar_para_d4sign_e_salvar, apolice.id)

    return {"status": "ok"}
