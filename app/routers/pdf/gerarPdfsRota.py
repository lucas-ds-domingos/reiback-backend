# app/routers/comissoes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import asyncio

from ...database import get_db
from ...models import Comissao, Usuario, Corretora, Assessoria
from ..gerar_pdf_assessoria import preparar_html_assessoria, gerar_pdf as gerar_pdf_assessoria
from ..gerarPdfComisao import preparar_html as preparar_html_corretor, gerar_pdf as gerar_pdf_corretor
from ..gerarPdfPagoAssessoria import preparar_htmlPago, gerar_pdfPago


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

    # 🔹 Busca dados do corretor
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # 🔹 Busca assessoria (se tiver)
    assessoria = None
    if usuario.assessoria_id:
        assessoria = db.query(Assessoria).filter(Assessoria.id == usuario.assessoria_id).first()

    # 🔹 Monta as comissões do corretor
    comissoes_dados = []
    for c in comissoes:
        apol = c.apolice
        prop = apol.proposta if apol else None
        tomador_nome = prop.tomador.nome if prop and prop.tomador else ""
        segurado_nome = prop.segurado.nome if prop and prop.segurado else ""
        comissoes_dados.append({
            "numero_apolice": apol.numero if apol else "",
            "tomador_nome": tomador_nome,
            "segurado_nome": segurado_nome,
            "premio": float(c.valor_premio or 0),
            "percentual": float(c.percentual_corretor or 0),
            "comissao_valor": float(c.valor_corretor or 0)
        })

        corretora = usuario.corretora  # pega a corretora vinculada ao usuário
        dados = {
            "corretor_nome": usuario.nome,
            "corretor_email": usuario.email,
            "corretor_telefone": corretora.telefone if corretora else "",
            "corretor_cnpj": corretora.cnpj if corretora else "",
            "assessoria_nome": assessoria.razao_social if assessoria else "",
            "assessoria_cnpj":assessoria.cnpj if assessoria else "",
            "comissoes": comissoes_dados
        }

    numeroDemonstrativo = f"{datetime.utcnow().strftime('%d/%m/%Y')}-{usuario_id}"
    html_content = preparar_html_corretor(dados, numeroDemonstrativo)

    tmpdir = tempfile.gettempdir()
    output_path = Path(tmpdir) / f"comissao_corretor_{usuario_id}_{int(datetime.utcnow().timestamp())}.pdf"

    await gerar_pdf_corretor(html_content, str(output_path))

    return FileResponse(
        str(output_path),
        filename=f"comissao_corretor_{usuario_id}.pdf",
        media_type="application/pdf"
    )

@router.get("/api/comissoes/pdf/pago/assessoria/{usuario_id}")
async def comissoes_pagas_assessoria(
    usuario_id: int,
    inicio: str = Query(..., description="Data inicial no formato YYYY-MM-DD"),
    fim: str = Query(..., description="Data final no formato YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    # valida usuário
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario or not usuario.assessoria_id:
        raise HTTPException(status_code=404, detail="Usuário não vinculado a assessoria")

    # converte datas
    try:
        data_inicio = datetime.strptime(inicio, "%Y-%m-%d")
        data_fim = datetime.strptime(fim, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD.")

    # busca comissões pagas
    comissoes = (
        db.query(Comissao)
        .filter(
            Comissao.assessoria_id == usuario.assessoria_id,
            Comissao.status_pagamento_assessoria == "pago",
            Comissao.data_pagamento_assessoria >= data_inicio,
            Comissao.data_pagamento_assessoria <= data_fim
        )
        .order_by(Comissao.data_pagamento_assessoria.asc())
        .all()
    )

    if not comissoes:
        raise HTTPException(status_code=404, detail="Nenhuma comissão paga encontrada neste período")

    # organiza por dia de pagamento
    dados_por_dia = {}
    for c in comissoes:
        dia = c.data_pagamento_assessoria.strftime("%d/%m/%Y")
        if dia not in dados_por_dia:
            dados_por_dia[dia] = []

        dados_por_dia[dia].append({
            "numero_apolice": c.apolice.numero if c.apolice else "",
            "tomador_nome": c.apolice.proposta.tomador.nome if c.apolice and c.apolice.proposta and c.apolice.proposta.tomador else "",
            "segurado_nome": c.apolice.proposta.segurado.nome if c.apolice and c.apolice.proposta and c.apolice.proposta.segurado else "",
            "premio": float(c.valor_premio or 0),
            "percentual": float(c.percentual_assessoria or 0),
            "comissao_valor": float(c.valor_assessoria or 0),
            "corretor_nome": c.apolice.proposta.usuario.nome if c.apolice and c.apolice.proposta and c.apolice.proposta.usuario else "",
            "data_pagamento": c.data_pagamento_assessoria  # ⬅️ datetime real para o template
        })

    # dados da assessoria
    dados_assessoria = {
        "id": usuario.assessoria_id,
        "nome_assessoria": usuario.assessoria.razao_social if usuario.assessoria else "",
        "cnpj": usuario.assessoria.cnpj if usuario.assessoria else "",
        "endereco": usuario.assessoria.endereco if usuario.assessoria else "",
        "cidade": usuario.assessoria.cidade if usuario.assessoria else "",
        "uf": usuario.assessoria.uf if usuario.assessoria else "",
        "cep": usuario.assessoria.cep if usuario.assessoria else "",
        "email": usuario.email if usuario.email else "-"
    }

    numero_demonstrativo = f"A-{usuario.assessoria_id}-{datetime.utcnow().strftime('%d%m%Y')}"
    html_content = preparar_htmlPago(dados_por_dia, numero_demonstrativo, tipo="assessoria", dados_assessoria=dados_assessoria)

    # gera PDF
    tmpdir = tempfile.gettempdir()
    output_path = Path(tmpdir) / f"comissoes_pagas_{usuario.assessoria_id}_{int(datetime.utcnow().timestamp())}.pdf"
    await gerar_pdfPago(html_content, str(output_path))

    return FileResponse(
        str(output_path),
        filename=f"comissoes_pagas_{usuario.assessoria_id}.pdf",
        media_type="application/pdf"
    )