# app/routers/comissoes_pdf.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ...database import get_db
from ...models import Comissao, Usuario, Apolice, Proposta
from ..gerarPdfComisao import preparar_html, gerar_pdf
import tempfile
from pathlib import Path


router = APIRouter()

@router.get("/pdf/corretor/{usuario_id}")
async def gerar_pdf_corretor(usuario_id: int, db: Session = Depends(get_db)):
    sete_dias_atras = datetime.utcnow() - timedelta(days=7)

    # Busca comissões pendentes do corretor
    comissoes = (
        db.query(Comissao)
        .join(Apolice, Comissao.apolice_id == Apolice.id)
        .join(Proposta, Apolice.proposta_id == Proposta.id)
        .filter(
            Comissao.corretor_id == usuario_id,
            Comissao.status_pagamento_corretor == "pendente",
            Comissao.created_at >= sete_dias_atras
        )
        .all()
    )

    if not comissoes:
        raise HTTPException(status_code=404, detail="Nenhuma comissão pendente nos últimos 7 dias")

    dados = []
    for c in comissoes:
        dados.append({
            "numero_apolice": c.apolice.numero,
            "tomador_nome": c.apolice.proposta.tomador.nome if c.apolice.proposta.tomador else "",
            "segurado_nome": c.apolice.proposta.segurado.nome if c.apolice.proposta.segurado else "",
            "corretor_nome": c.corretor.nome if c.corretor else "",
            "premio": float(c.valor_premio or 0),
            "percentual": float(c.percentual_corretor or 0),
            "comissao_valor": float(c.valor_corretor or 0),
        })

    numero_demonstrativo = f"C-{usuario_id}-{datetime.utcnow().strftime('%d%m%Y')}"
    html = preparar_html(dados, numero_demonstrativo)

    tmpdir = tempfile.gettempdir()
    output_path = Path(tmpdir) / f"comissao_corretor_{usuario_id}_{int(datetime.utcnow().timestamp())}.pdf"
    await gerar_pdf(html, str(output_path))

    return FileResponse(
        str(output_path),
        filename=f"comissao_corretor_{usuario_id}.pdf",
        media_type="application/pdf"
    )
