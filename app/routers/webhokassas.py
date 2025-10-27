from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta, Apolice, Comissao
from datetime import datetime
from decimal import Decimal
from .d4sign_tasks import enviar_para_d4sign_e_salvar
import random

router = APIRouter()


def gerar_numero_apolice(db: Session):
    existentes = db.query(Apolice.numero).all()
    existentes = {num[0] for num in existentes}

    ultimo = db.query(Apolice).order_by(Apolice.id.desc()).first()
    ultimo_num = 0
    if ultimo:
        try:
            ultimo_num = int(ultimo.numero[-5:])
        except ValueError:
            ultimo_num = ultimo.id

    for _ in range(100):
        prefixo = random.randint(100, 999)
        numero = f"FIN-{prefixo}{ultimo_num + 1:05d}"
        if numero not in existentes:
            return numero

    # fallback
    return f"FIN-{random.randint(100, 999)}{ultimo_num + 1:05d}"


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
    proposta.valor_pago = Decimal(str(payment.get("netValue", payment.get("value", 0))))
    if payment.get("paymentDate"):
        proposta.pago_em = datetime.strptime(payment["paymentDate"], "%Y-%m-%d")
    db.commit()
    db.refresh(proposta)

    # Verifica se a apólice já existe
    apolice = db.query(Apolice).filter(Apolice.proposta_id == proposta.id).first()
    if not apolice:
        # Cria apólice nova
        numero_apolice = gerar_numero_apolice(db)
        apolice = Apolice(
            proposta_id=proposta.id,
            numero=numero_apolice,
            data_criacao=datetime.utcnow(),
            status_assinatura="pendente"
        )
        db.add(apolice)
        db.commit()
        db.refresh(apolice)

        # -------------------------
        # CÁLCULO DE COMISSÕES
        # -------------------------
        valor_premio = proposta.premio or Decimal("0.00")
        comissao_base = valor_premio * (proposta.comissao_percentual / 100)

        comissoes = []

        usuario = proposta.usuario

        # Corretor
        if usuario.role == "corretor":
            comissoes.append(
                Comissao(
                    apolice_id=apolice.id,
                    corretor_id=usuario.id,
                    valor_corretor=comissao_base,
                    percentual_corretor=proposta.comissao_percentual,
                    valor_premio=valor_premio
                )
            )

            # Assessoria vinculada
            if usuario.assessoria:
                percentual_assessoria_total = proposta.comissao_percentual * (usuario.assessoria.comissao / 100)
                valor_assessoria = valor_premio * (percentual_assessoria_total / 100)
                comissoes.append(
                    Comissao(
                        apolice_id=apolice.id,
                        assessoria_id=usuario.assessoria.id,
                        valor_assessoria=valor_assessoria,
                        percentual_assessoria=percentual_assessoria_total,
                        valor_premio=valor_premio
                    )
                )

        # Usuário é assessoria diretamente
        elif usuario.role == "assessoria" and usuario.assessoria:
            percentual_assessoria_total = proposta.comissao_percentual * (usuario.assessoria.comissao / 100)
            valor_assessoria = valor_premio * (percentual_assessoria_total / 100)
            comissoes.append(
                Comissao(
                    apolice_id=apolice.id,
                    assessoria_id=usuario.assessoria.id,
                    valor_assessoria=valor_assessoria,
                    percentual_assessoria=percentual_assessoria_total,
                    valor_premio=valor_premio
                )
            )

        # Adiciona todas as comissões de uma vez
        db.add_all(comissoes)
        db.commit()

        # Envia para D4Sign
        background_tasks.add_task(enviar_para_d4sign_e_salvar, apolice.id)

    return {"status": "ok", "apolice_numero": apolice.numero}
