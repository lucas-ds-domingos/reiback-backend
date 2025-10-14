from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.database import get_db
from app.models import Proposta, Apolice, Usuario
from typing import Optional

router = APIRouter()

def get_user_filter(user: Usuario):
    """
    Retorna o filtro de propostas de acordo com o usuário logado.
    """
    if user.role == "master":
        return True  # sem filtro, vê tudo
    elif user.role == "assessoria":
        return Proposta.usuario.has(assessoria_id=user.assessoria_id)
    else:  # corretor
        return Proposta.usuario_id == user.id

@router.get("/dashboard")
def get_dashboard(current_user: Usuario = Depends(get_db), db: Session = Depends(get_db)):
    now = datetime.now()
    start_month = datetime(now.year, now.month, 1)

    # Filtro de acordo com usuário
    user_filter = get_user_filter(current_user)

    # Contagem por status
    total_emitidas = db.query(Proposta).filter(
        user_filter,
        Proposta.status == "aprovada",
        Proposta.cancelada_em.is_(None)
    ).count()

    total_canceladas = db.query(Proposta).filter(
        user_filter,
        Proposta.cancelada_em.isnot(None)
    ).count()

    total_aguardando_pagamento = db.query(Proposta).filter(
        user_filter,
        Proposta.status == "aprovada",
        Proposta.cancelada_em.is_(None),
        Proposta.pago_em.is_(None),
        Proposta.link_pagamento.isnot(None)
    ).count()

    total_pagas = db.query(Proposta).filter(
        user_filter,
        Proposta.pago_em.isnot(None)
    ).count()

    # Valores do mês atual
    revenue_this_month = db.query(func.sum(Proposta.premio)).filter(
        user_filter,
        Proposta.pago_em >= start_month
    ).scalar() or 0

    # Comissão do mês atual (somente paga pelo master ou corretor, assessoria não vê)
    commission_filter = user_filter
    if current_user.role == "assessoria":
        commission_to_pay = None
    else:
        commission_to_pay = db.query(func.sum(Proposta.comissao_valor)).filter(
            commission_filter,
            Proposta.pago_em >= start_month
        ).scalar() or 0

    # Série mensal
    monthly_series = []
    for month in range(1, 13):
        start = datetime(now.year, month, 1)
        end = datetime(now.year, month, 28)

        emitidas_mes = db.query(Proposta).filter(
            user_filter,
            Proposta.status == "aprovada",
            Proposta.cancelada_em.is_(None),
            Proposta.data_criacao >= start,
            Proposta.data_criacao <= end
        ).count()

        canceladas_mes = db.query(Proposta).filter(
            user_filter,
            Proposta.cancelada_em.isnot(None),
            Proposta.cancelada_em >= start,
            Proposta.cancelada_em <= end
        ).count()

        aguardando_pag_mes = db.query(Proposta).filter(
            user_filter,
            Proposta.status == "aprovada",
            Proposta.cancelada_em.is_(None),
            Proposta.pago_em.is_(None),
            Proposta.link_pagamento.isnot(None),
            Proposta.data_criacao >= start,
            Proposta.data_criacao <= end
        ).count()

        pagas_mes = db.query(Proposta).filter(
            user_filter,
            Proposta.pago_em.isnot(None),
            Proposta.pago_em >= start,
            Proposta.pago_em <= end
        ).count()

        monthly_series.append({
            "month": start.strftime("%b"),
            "emitidas": emitidas_mes,
            "canceladas": canceladas_mes,
            "aguardandoPagamento": aguardando_pag_mes,
            "pagas": pagas_mes
        })

    # Distribuição status para gráfico de pizza
    status_distribution = [
        {"name": "Emitidas", "value": total_emitidas},
        {"name": "Aguardando Pagamento", "value": total_aguardando_pagamento},
        {"name": "Pagas", "value": total_pagas},
        {"name": "Canceladas", "value": total_canceladas},
    ]

    return {
        "emitidas": total_emitidas,
        "canceladas": total_canceladas,
        "aguardandoPagamento": total_aguardando_pagamento,
        "pagas": total_pagas,
        "revenueThisMonth": revenue_this_month,
        "commissionToPay": commission_to_pay,
        "monthlySeries": monthly_series,
        "statusDistribution": status_distribution
    }
