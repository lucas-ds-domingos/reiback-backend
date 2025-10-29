from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta, Apolice, Comissao
from datetime import datetime
from decimal import Decimal
import random
from .d4sign_tasks import enviar_para_d4sign_e_salvar

router = APIRouter()


def gerar_numero_apolice(db: Session) -> str:
    """
    Gera um número único de apólice: FIN-{prefixo aleatório de 3 dígitos}{sequência 5 dígitos}
    """
    existentes = db.query(Apolice.numero).all()
    existentes = {num[0] for num in existentes}

    ultimo = db.query(Apolice).order_by(Apolice.id.desc()).first()
    if ultimo:
        try:
            ultimo_num = int(ultimo.numero[-5:])
        except ValueError:
            ultimo_num = ultimo.id
    else:
        ultimo_num = 0

    for _ in range(100):
        prefixo = random.randint(100, 999)
        numero = f"FIN-{prefixo}{ultimo_num + 1:05d}"
        if numero not in existentes:
            return numero

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
    proposta.valor_pago = Decimal(str(payment.get("netValue", payment.get("value"))))
    if payment.get("paymentDate"):
        proposta.pago_em = datetime.strptime(payment["paymentDate"], "%Y-%m-%d")
    db.commit()
    db.refresh(proposta)

    # Verifica se a apólice já existe
    apolice = db.query(Apolice).filter(Apolice.proposta_id == proposta.id).first()
    if not apolice:
        # Cria nova apólice
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

        # Calcular comissões com base no valor do prêmio
        valor_premio = proposta.premio or Decimal("0.00")
        comissoes = []

        usuario = proposta.usuario

        # Comissão do corretor
        if usuario.role == "corretor":
            valor_corretor = valor_premio * (proposta.comissao_percentual / 100)
            comissoes.append(
                Comissao(
                    apolice_id=apolice.id,
                    corretor_id=usuario.id,
                    valor_corretor=valor_corretor,
                    percentual_corretor=proposta.comissao_percentual,
                    valor_assessoria=Decimal("0.00"),
                    percentual_assessoria=Decimal("0.00"),
                    valor_premio=valor_premio
                )
            )

        # Comissão da assessoria (ajustada conforme quem criou a proposta)
        if usuario.assessoria:
            if usuario.role == "corretor":
                # Corretor criou → assessoria ganha só a porcentagem dela
                percentual_assessoria = usuario.assessoria.comissao or Decimal("0.00")
            else:
                # Assessoria criou → soma a porcentagem dela + da proposta
                percentual_assessoria = (proposta.comissao_percentual or Decimal("0.00")) + (
                    usuario.assessoria.comissao or Decimal("0.00")
                )

            valor_assessoria = valor_premio * (percentual_assessoria / 100)
            comissoes.append(
                Comissao(
                    apolice_id=apolice.id,
                    assessoria_id=usuario.assessoria.id,
                    valor_corretor=Decimal("0.00"),
                    percentual_corretor=Decimal("0.00"),
                    valor_assessoria=valor_assessoria,
                    percentual_assessoria=percentual_assessoria,
                    valor_premio=valor_premio
                )
            )

        db.add_all(comissoes)
        db.commit()

        # Envia para D4Sign apenas se a apólice foi criada agora
        background_tasks.add_task(enviar_para_d4sign_e_salvar, apolice.id)

    return {"status": "ok", "apolice_numero": apolice.numero}
