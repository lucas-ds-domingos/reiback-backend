from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.database import get_db
from app.models import Proposta, Apolice

router = APIRouter()

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    now = datetime.now()
    start_month = datetime(now.year, now.month, 1)

    # Contagem de propostas
    total_proposals = db.query(Proposta).count()
    proposals_paid = db.query(Proposta).filter(Proposta.pago_em != None).count()
    proposals_draft = db.query(Proposta).filter(Proposta.status == "rascunho").count()
    proposals_rejected = db.query(Proposta).filter(Proposta.status == "rejeitada").count()

    # Apólices geradas
    policies_total = db.query(Apolice).count()

    # Valores e comissão
    revenue_this_month = db.query(func.sum(Proposta.premio)).filter(
        Proposta.pago_em >= start_month
    ).scalar() or 0

    commission_to_pay = db.query(func.sum(Proposta.comissao_valor)).filter(
        Proposta.pago_em != None
    ).scalar() or 0

    # Série mensal para gráfico
    monthly_series = []
    for month in range(1, 13):
        start = datetime(now.year, month, 1)
        end = datetime(now.year, month, 28)
        month_revenue = db.query(func.sum(Proposta.premio)).filter(
            Proposta.pago_em >= start,
            Proposta.pago_em <= end
        ).scalar() or 0
        month_proposals = db.query(Proposta).filter(
            Proposta.pago_em >= start,
            Proposta.pago_em <= end
        ).count()
        monthly_series.append({"month": start.strftime("%b"), "revenue": month_revenue, "proposals": month_proposals})

    # Distribuição status
    status_distribution = [
        {"name": "Rascunho", "value": proposals_draft},
        {"name": "Aprovada/Paga", "value": proposals_paid},
        {"name": "Rejeitada", "value": proposals_rejected},
    ]

    return {
        "totalProposals": total_proposals,
        "proposalsPaid": proposals_paid,
        "proposalsDraft": proposals_draft,
        "proposalsRejected": proposals_rejected,
        "policiesTotal": policies_total,
        "revenueThisMonth": revenue_this_month,
        "commissionToPay": commission_to_pay,
        "monthlySeries": monthly_series,
        "statusDistribution": status_distribution
    }
