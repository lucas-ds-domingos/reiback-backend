# app/routers/comissoes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import asyncio

from ...database import get_db
from ...models import Comissao, Usuario, Corretora
from ..gerar_pdf_assessoria import preparar_html_assessoria, gerar_pdf as gerar_pdf_assessoria
from ..gerarPdfComisao import preparar_html as preparar_html_corretor, gerar_pdf as gerar_pdf_corretor


router = APIRouter()


# ---------------------------
# PDF Assessoria
# ---------------------------
@router.get("/api/pdf/assessoria/{usuario_id}")
async def pdf_assessoria(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.assessoria_id:
        raise HTTPException(status_code=404, detail="Usuário não vinculado a assessoria")

    sete_dias_atras = datetime.utcnow() - timedelta(days=7)

    comissoes = (
        db.query(Comissao)
        .filter(
            Comissao.assessoria_id == usuario.assessoria_id,
            Comissao.status_pagamento_assessoria == "pendente",
            Comissao.created_at >= sete_dias_atras
        )
        .all()
    )

    if not comissoes:
        raise HTTPException(status_code=404, detail="Nenhuma comissão pendente nos últimos 7 dias")

    # Preparar dados para o HTML
    dados = []
    for c in comissoes:
        dados.append({
            "numero_apolice": c.apolice.numero if c.apolice else "",
            "tomador_nome": c.apolice.proposta.tomador.nome if c.apolice and c.apolice.proposta and c.apolice.proposta.tomador else "",
            "segurado_nome": c.apolice.proposta.segurado.nome if c.apolice and c.apolice.proposta and c.apolice.proposta.segurado else "",
            "premio": float(c.valor_premio or 0),
            "percentual": float(c.percentual_assessoria or 0),
            "comissao_valor": float(c.valor_assessoria or 0),
            "corretor_nome": c.apolice.proposta.usuario.nome if c.apolice and c.apolice.proposta and c.apolice.proposta.usuario else ""
        })

    dados_assessoria = {
        "id": usuario.assessoria_id,
        "nome_assessoria": usuario.assessoria.razao_social if usuario.assessoria else "",
        "cnpj": usuario.assessoria.cnpj if usuario.assessoria else "",
        "endereco": usuario.assessoria.endereco if usuario.assessoria else "",
        "cidade": usuario.assessoria.cidade if usuario.assessoria else "",
        "uf": usuario.assessoria.uf if usuario.assessoria else "",
        "cep": usuario.assessoria.cep if usuario.assessoria else "",
        "email": usuario.email if usuario and usuario.email else "-"
    }

    numero_demonstrativo = f"A-{usuario.assessoria_id}-{datetime.utcnow().strftime('%d%m%Y')}"
    html_content = preparar_html_assessoria(dados, numero_demonstrativo, dados_assessoria)

    tmpdir = tempfile.gettempdir()
    output_path = Path(tmpdir) / f"comissao_assessoria_{usuario.assessoria_id}_{int(datetime.utcnow().timestamp())}.pdf"

    await gerar_pdf_assessoria(html_content, str(output_path)) 

    return FileResponse(
        str(output_path),
        filename=f"comissao_assessoria_{usuario.assessoria_id}.pdf",
        media_type="application/pdf"
    )


# ---------------------------
# PDF Corretor
# ---------------------------
@router.get("/api/pdf/corretor/{usuario_id}")
async def pdf_corretor(usuario_id: int, db: Session = Depends(get_db)):
    sete_dias_atras = datetime.utcnow() - timedelta(days=7)

    comissoes = (
        db.query(Comissao)
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
        apol = c.apolice
        prop = apol.proposta if apol else None
        tomador_nome = prop.tomador.nome if prop and prop.tomador else ""
        segurado_nome = prop.segurado.nome if prop and prop.segurado else ""
        dados.append({
            "numero_apolice": apol.numero if apol else "",
            "tomador_nome": tomador_nome,
            "segurado_nome": segurado_nome,
            "premio": float(c.valor_premio or 0),
            "percentual": float(c.percentual_corretor or 0),
            "comissao_valor": float(c.valor_corretor or 0)
        })

    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    numero_demonstrativo = f"{datetime.utcnow().strftime('%d/%m/%Y')}-{usuario_id}"
    html_content = preparar_html_corretor(dados, numero_demonstrativo)

    tmpdir = tempfile.gettempdir()
    output_path = Path(tmpdir) / f"comissao_corretor_{usuario_id}_{int(datetime.utcnow().timestamp())}.pdf"

    await gerar_pdf_corretor(html_content, str(output_path)) 

    return FileResponse(
        str(output_path),
        filename=f"comissao_corretor_{usuario_id}.pdf",
        media_type="application/pdf"
    )
