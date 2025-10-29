# app/routers/comissoes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..gerarPdfComisao import preparar_html, gerar_pdf
from ..gerar_pdf_assessoria import preparar_html_assessoria
from ...database import get_db
from ...models import Comissao, Apolice, Usuario
import tempfile
from pathlib import Path


router = APIRouter()


@router.get("/pdf/comisao/{usuario_id}")
async def gerar_pdf_unico(usuario_id: int, db: Session = Depends(get_db)):
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    sete_dias_atras = datetime.utcnow() - timedelta(days=7)

    # --------- Assessoria ---------
    if usuario.assessoria_id:
        comissoes = (
            db.query(Comissao)
            .join(Usuario, Comissao.corretor_id == Usuario.id)
            .filter(
                Usuario.assessoria_id == usuario.assessoria_id,
                Comissao.status_pagamento_assessoria == "pendente",
                Comissao.apolice.has(Apolice.data_criacao >= sete_dias_atras)
            )
            .all()
        )

        if not comissoes:
            raise HTTPException(status_code=404, detail="Nenhuma comissão pendente")

        dados = [{
            "numero_apolice": c.apolice.numero,
            "tomador_nome": c.apolice.proposta.tomador.nome,
            "segurado_nome": c.apolice.proposta.segurado.nome,
            "corretor_nome": c.corretor.nome if c.corretor else "-",
            "premio": float(c.valor_premio),
            "percentual": float(c.percentual_assessoria),
            "comissao_valor": float(c.valor_assessoria),
        } for c in comissoes]

        dados_assessoria = {
            "id": usuario.assessoria_id,
            "nome_assessoria": usuario.assessoria.razao_social if usuario.assessoria else "",
            "cnpj": usuario.assessoria.cnpj if usuario.assessoria else "",
        }

        numero_demonstrativo = f"A-{usuario.assessoria_id}-{datetime.utcnow().strftime('%d%m%Y')}"
        html = preparar_html_assessoria(dados, numero_demonstrativo, dados_assessoria)

        tmpdir = tempfile.gettempdir()
        output_path = Path(tmpdir) / f"comissao_assessoria_{usuario.assessoria_id}_{int(datetime.utcnow().timestamp())}.pdf"
        await gerar_pdf(html, str(output_path))

        return FileResponse(str(output_path), filename=f"comissao_assessoria_{usuario.assessoria_id}.pdf", media_type="application/pdf")

    # --------- Corretor ---------
    else:
        comissoes = (
            db.query(Comissao)
            .filter(
                Comissao.corretor_id == usuario_id,
                Comissao.status_pagamento_corretor == "pendente",
                Comissao.apolice.has(Apolice.data_criacao >= sete_dias_atras)
            )
            .all()
        )

        if not comissoes:
            raise HTTPException(status_code=404, detail="Nenhuma comissão pendente")

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
                "comissao_valor": float(c.valor_corretor or 0),
            })

        numero_demonstrativo = f"{datetime.utcnow().strftime('%d/%m/%Y')}-{usuario_id}"
        html = preparar_html(dados, numero_demonstrativo)

        tmpdir = tempfile.gettempdir()
        output_path = Path(tmpdir) / f"comissao_corretor_{usuario_id}_{int(datetime.utcnow().timestamp())}.pdf"
        await gerar_pdf(html, str(output_path))

        return FileResponse(str(output_path), filename=f"comissao_{usuario_id}.pdf", media_type="application/pdf")
