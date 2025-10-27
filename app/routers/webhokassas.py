from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta, Apolice, Comissao
from datetime import datetime
from decimal import Decimal
import random
from .d4sign_tasks import enviar_para_d4sign_e_salvar

router = APIRouter()

def gerar_numero_apolice(db: Session):
    """Gera um número de apólice único no formato FIN-XXXNNNNN"""
    ultima = db.query(Apolice).order_by(Apolice.id.desc()).first()
    sequencia = (int(ultima.numero[-5:]) if ultima else 0) + 1
    for _ in range(100):
        prefixo = random.randint(100, 999)
        numero = f"FIN-{prefixo}{sequencia:05d}"
        if not db.query(Apolice).filter(Apolice.numero == numero).first():
            return numero
    # fallback
    return f"FIN-{random.randint(100, 999)}{sequencia:05d}"

@router.post("/webhook-asaas")
def asaas_webhook(payload: dict, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    event = payload.get("event")
    payment = payload.get("payment", {})

    if event != "PAYMENT_RECEIVED":
        return {"status": "ignored"}

    # identifica a proposta
    try:
        proposta_id = int(payment.get("externalReference"))
    except (TypeError, ValueError):
        return {"status": "ignored"}

    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        return {"status": "proposta not found"}

    # atualiza status da proposta
    proposta.status = "paga"
    proposta.valor_pago = Decimal(str(payment.get("netValue", payment.get("value", 0))))
    if payment.get("paymentDate"):
        proposta.pago_em = datetime.strptime(payment["paymentDate"], "%Y-%m-%d")

    # verifica se já existe apólice
    apolice = db.query(Apolice).filter(Apolice.proposta_id == proposta.id).first()
    if not apolice:
        # cria apólice
        numero_apolice = gerar_numero_apolice(db)
        apolice = Apolice(
            proposta_id=proposta.id,
            numero=numero_apolice,
            data_criacao=datetime.utcnow(),
            status_assinatura="pendente"
        )
        db.add(apolice)
        db.flush()  # gera ID sem commitar ainda

        usuario = proposta.usuario
        comissao_padrao = (proposta.valor_pago or Decimal("0.00")) * (proposta.comissao_percentual / 100)
        comissoes = []

        # comissão corretor
        if usuario.role == "corretor":
            comissoes.append(Comissao(
                apolice_id=apolice.id,
                corretor_id=usuario.id,
                valor_corretor=comissao_padrao,
                percentual_corretor=proposta.comissao_percentual
            ))
            if usuario.assessoria:
                comissoes.append(Comissao(
                    apolice_id=apolice.id,
                    assessoria_id=usuario.assessoria.id,
                    valor_assessoria=comissao_padrao * (usuario.assessoria.comissao / 100),
                    percentual_assessoria=usuario.assessoria.comissao
                ))

        # comissão assessoria direta
        elif usuario.role == "assessoria" and usuario.assessoria:
            comissoes.append(Comissao(
                apolice_id=apolice.id,
                assessoria_id=usuario.assessoria.id,
                valor_assessoria=comissao_padrao,
                percentual_assessoria=usuario.assessoria.comissao
            ))

        # adiciona todas comissões
        for com in comissoes:
            db.add(com)

        # commit final
        db.commit()
        db.refresh(apolice)

        # envia para D4Sign
        background_tasks.add_task(enviar_para_d4sign_e_salvar, apolice.id)

    else:
        # apenas atualiza proposta paga se a apólice já existia
        db.commit()

    return {"status": "ok", "apolice_numero": apolice.numero}
