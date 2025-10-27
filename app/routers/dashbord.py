from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, extract
from datetime import datetime
import calendar

from ..database import get_db
from ..models import Proposta, Apolice, Usuario

router = APIRouter()


def get_user_filter(user: Usuario):
    """Retorna um filtro SQLAlchemy para aplicar de acordo com a role"""
    if user.role == "master":
        return True
    elif user.role == "assessoria":
        return Proposta.usuario.has(Usuario.assessoria_id == user.assessoria_id)
    else:
        return Proposta.usuario_id == user.id


def get_current_user(
    x_user_id: int = Header(...),
    x_user_role: str = Header(...),
    db: Session = Depends(get_db)
):
    user = db.query(Usuario).filter(Usuario.id == x_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuário não encontrado")
    user.role = x_user_role
    return user


@router.get("/dashboard")
def get_dashboard(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now()
    start_of_year = datetime(now.year, 1, 1)
    filtro = get_user_filter(current_user)

    # ---------------------------
    # Contagens gerais
    # ---------------------------
    total_proposals = db.query(Proposta).filter(filtro).count()
    proposals_paid = db.query(Proposta).filter(filtro, Proposta.pago_em != None).count()
    proposals_draft = db.query(Proposta).filter(filtro, Proposta.status == "rascunho").count()
    proposals_rejected = db.query(Proposta).filter(filtro, Proposta.status == "rejeitada").count()
    proposals_pending_payment = db.query(Proposta).filter(
        filtro, Proposta.status == "aprovada", Proposta.pago_em == None
    ).count()
    proposals_canceled = db.query(Proposta).filter(filtro, Proposta.status == "cancelada").count()
    policies_total = db.query(Apolice).filter(Apolice.proposta.has(filtro)).count()

    # ---------------------------
    # Receita e comissão do mês atual
    # ---------------------------
    start_month = datetime(now.year, now.month, 1)
    revenue_this_month = db.query(func.sum(Proposta.premio)).filter(
        filtro,
        Proposta.pago_em != None,
        Proposta.pago_em >= start_month
    ).scalar() or 0

    commission_to_pay = 0
    if current_user.role != "assessoria":
        commission_to_pay = db.query(func.sum(Proposta.comissao_valor)).filter(
            filtro,
            Proposta.pago_em != None,
            Proposta.pago_em >= start_month
        ).scalar() or 0

    # ---------------------------
    # Série mensal otimizada (uma query)
    # ---------------------------
    monthly_data = (
        db.query(
            extract("month", Proposta.data_criacao).label("month"),
            func.count(Proposta.id).label("proposals"),
            func.coalesce(func.sum(Proposta.premio), 0).label("revenue")
        )
        .filter(filtro, Proposta.data_criacao >= start_of_year)
        .group_by("month")
        .all()
    )

    # Montando a lista de 12 meses
    monthly_series = []
    for month in range(1, 13):
        month_info = next((m for m in monthly_data if int(m.month) == month), None)
        monthly_series.append({
            "month": datetime(now.year, month, 1).strftime("%b"),
            "revenue": float(month_info.revenue) if month_info else 0,
            "proposals": month_info.proposals if month_info else 0,
        })

    # ---------------------------
    # Distribuição por status (uma query)
    # ---------------------------
    status_counts = (
        db.query(Proposta.status, func.count(Proposta.id))
        .filter(filtro)
        .group_by(Proposta.status)
        .all()
    )
    status_map = {status: count for status, count in status_counts}
    status_distribution = [
        {"name": "Rascunho", "value": status_map.get("rascunho", 0)},
        {"name": "Emitida / Aguardando pagamento", "value": status_map.get("aprovada", 0)},
        {"name": "Paga", "value": status_map.get("pago", 0) or proposals_paid},  # fallback
        {"name": "Cancelada", "value": status_map.get("cancelada", 0)},
    ]

    # ---------------------------
    # Retorno
    # ---------------------------
    return {
        "totalProposals": total_proposals,
        "proposalsDraft": proposals_draft,
        "proposalsPending": proposals_pending_payment,
        "proposalsPaid": proposals_paid,
        "proposalsCancelled": proposals_canceled,
        "policiesTotal": policies_total,
        "revenueThisMonth": float(revenue_this_month),
        "commissionToPay": float(commission_to_pay),
        "monthlySeries": monthly_series,
        "statusDistribution": status_distribution,
    }
