# app/routers/comissoes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..gerarPdfComisao import preparar_html, gerar_pdf
from ..gerar_pdf_assessoria import preparar_html_assessoria
from ...database import get_db
from ...models import Comissao, Apolice, Proposta, Usuario, Corretora, Assessoria
import tempfile
from pathlib import Path

router = APIRouter()

# ---------------------------
# Listar comissões pendentes
# ---------------------------
@router.get("/comissoes/pendentes")
def listar_comissoes_pendentes(db: Session = Depends(get_db)):
    comissoes = db.query(Comissao).filter(
        (Comissao.status_pagamento_corretor == "pendente") |
        (Comissao.status_pagamento_assessoria == "pendente")
    ).all()

    resultados = []
    for c in comissoes:
        resultados.append({
            "id": c.id,
            "apolice_numero": c.apolice.numero,
            "tomador": c.apolice.proposta.tomador.nome,
            "segurado": c.apolice.proposta.segurado.nome,
            "premio": float(c.valor_premio),
            "percentual_corretor": float(c.percentual_corretor),
            "valor_corretor": float(c.valor_corretor),
            "percentual_assessoria": float(c.percentual_assessoria),
            "valor_assessoria": float(c.valor_assessoria),
            "corretor": c.corretor.nome if c.corretor else None,
            "corretor_id": c.corretor.id if c.corretor else None,
            "assessoria": c.assessoria.razao_social if c.assessoria else None,
            "assessoria_id": c.assessoria.id if c.assessoria else None
        })
    return resultados

# ---------------------------
# Marcar comissão como paga
# ---------------------------
@router.post("/comissoes/marcar_pago/{comissao_id}")
def marcar_pago(comissao_id: int, tipo: str, db: Session = Depends(get_db)):
    comissao = db.query(Comissao).filter(Comissao.id == comissao_id).first()
    if not comissao:
        return {"error": "Comissão não encontrada"}

    if tipo == "corretor":
        comissao.status_pagamento_corretor = "pago"
        comissao.data_pagamento_corretor = datetime.utcnow()
    elif tipo == "assessoria":
        comissao.status_pagamento_assessoria = "pago"
        comissao.data_pagamento_assessoria = datetime.utcnow()
    else:
        return {"error": "Tipo inválido"}

    db.commit()
    return {"status": "ok"}


@router.post("/comissoes/marcar_todas")
def marcar_todas(tipo: str, usuario_id: int, db: Session = Depends(get_db)):

    if tipo not in ["corretor", "assessoria"]:
        return {"error": "Tipo inválido"}

    if tipo == "corretor":
        comissoes = db.query(Comissao).filter(
            Comissao.corretor_id == usuario_id,
            Comissao.status_pagamento_corretor != "pago"
        ).all()
        for c in comissoes:
            c.status_pagamento_corretor = "pago"
            c.data_pagamento_corretor = datetime.utcnow()
    else:  # assessoria
        comissoes = db.query(Comissao).filter(
            Comissao.assessoria_id == usuario_id,
            Comissao.status_pagamento_assessoria != "pago"
        ).all()
        for c in comissoes:
            c.status_pagamento_assessoria = "pago"
            c.data_pagamento_assessoria = datetime.utcnow()

    db.commit()
    return {"status": "ok", "total": len(comissoes)}
