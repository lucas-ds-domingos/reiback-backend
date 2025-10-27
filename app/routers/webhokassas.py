from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta, Apolice, Comissao, Usuario
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

    # Calcula comissões
    usuario = proposta.usuario
    comissao_corretor = Decimal("0.00")
    comissao_assessoria = Decimal("0.00")

    # Comissão padrão 20% do valor pago
    comissao_padrao = (proposta.valor_pago or Decimal("0.00")) * (proposta.comissao_percentual / 100)

    if usuario.role == "corretor":
        comissao_corretor = comissao_padrao
        if usuario.assessoria:
            comissao_assessoria = comissao_padrao * (usuario.assessoria.comissao / 100)
    elif usuario.role == "assessoria":
        # Assesoria que gera: recebe 20% + % dela própria
        comissao_corretor = comissao_padrao
        comissao_assessoria = comissao_padrao * (usuario.comissao / 100)  # % própria da assessoria

    # Salva comissões na tabela
    if comissao_corretor > 0:
        comissao = Comissao(
            apolice_id=apolice.id,
            usuario_id=usuario.id if usuario.role == "corretor" else None,
            assessoria_id=None if usuario.role == "corretor" else usuario.id,
            valor=comissao_corretor,
            pago=False
        )
        db.add(comissao)

    if comissao_assessoria > 0 and usuario.assessoria:
        comissao = Comissao(
            apolice_id=apolice.id,
            usuario_id=None,
            assessoria_id=usuario.assessoria.id,
            valor=comissao_assessoria,
            pago=False
        )
        db.add(comissao)

    db.commit()

    # Chama função em background para gerar PDF e enviar ao D4Sign
    background_tasks.add_task(enviar_para_d4sign_e_salvar, apolice.id)

    return {"status": "ok"}
