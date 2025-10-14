from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from app.database import get_db
from app.models import Proposta, Apolice, Usuario

router = APIRouter()

def get_user_filter(user: Usuario):
    """Retorna um filtro SQLAlchemy para aplicar de acordo com a role"""
    if user.role == "master":
        return True  # Master vê tudo
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
    # Atualiza a role do usuário baseado no header
    user.role = x_user_role
    return user

@router.get("/dashboard")
def get_dashboard(
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now()
    start_month = datetime(now.year, now.month, 1)

    filtro = get_user_filter(current_user)

    # Contagem de propostas
    total_proposals = db.query(Proposta).filter(filtro).count()
    proposals_draft = db.query(Proposta).filter(filtro, Proposta.status == "rascunho").count()
    proposals_rejected = db.query(Proposta).filter(filtro, Proposta.status == "rejeitada").count()
    proposals_canceled = db.query(Proposta).filter(filtro, Proposta.status == "cancelada").count()
    proposals_paid = db.query(Proposta).filter(filtro, Proposta.pago_em != None).count()
    
    # Emitidas e aguardando pagamento (status "aprovada" e não pagas)
    proposals_pending_payment = db.query(Proposta).filter(filtro, Proposta.status == "aprovada", Proposta.pago_em == None).count()
    proposals_emitted = proposals_pending_payment  # mesmo valor para exibir no gráfico

    # Apólices geradas
    policies_total = db.query(Apolice).filter(Apolice.proposta.has(filtro)).count()

    # Valores e comissão do mês atual
    revenue_this_month = db.query(func.sum(Proposta.premio)).filter(
        filtro,
        Proposta.pago_em != None,
        Proposta.pago_em >= start_month
    ).scalar() or 0

    # Comissão do mês (apenas para quem não é assessoria)
    commission_to_pay = 0
    if current_user.role != "assessoria":
        commission_to_pay = db.query(func.sum(Proposta.comissao_valor)).filter(
            filtro,
            Proposta.pago_em != None,
            Proposta.pago_em >= start_month
        ).scalar() or 0

    # Série mensal para gráfico
    monthly_series = []
    for month in range(1, 13):
        start = datetime(now.year, month, 1)
        end = datetime(now.year, month, 28)
        month_revenue = db.query(func.sum(Proposta.premio)).filter(
            filtro,
            Proposta.pago_em != None,
            Proposta.pago_em >= start,
            Proposta.pago_em <= end
        ).scalar() or 0
        month_proposals = db.query(Proposta).filter(
            filtro,
            Proposta.data_criacao >= start,
            Proposta.data_criacao <= end
        ).count()
        monthly_series.append({"month": start.strftime("%b"), "revenue": month_revenue, "proposals": month_proposals})

    # Distribuição por status
    status_distribution = [
        {"name": "Rascunho", "value": proposals_draft},
        {"name": "Emitida", "value": proposals_emitted},
        {"name": "Aguardando pagamento", "value": proposals_pending_payment},
        {"name": "Paga", "value": proposals_paid},
        {"name": "Cancelada", "value": proposals_canceled},
    ]

    return {
        "totalProposals": total_proposals,
        "policiesTotal": policies_total,
        "revenueThisMonth": revenue_this_month,
        "commissionToPay": commission_to_pay,
        "monthlySeries": monthly_series,
        "statusDistribution": status_distribution,
    }
