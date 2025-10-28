# app/routers/comissoes.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..gerarPdfComisao import preparar_html, gerar_pdf
from ...database import get_db
from ...models import Comissao, Apolice, Proposta
import tempfile
from pathlib import Path

router = APIRouter()

@router.get("/comissoes/pendentes")
def listar_comissoes_pendentes(db: Session = Depends(get_db)):
    # retorna todas as comissões pendentes
    sete_dias_atras = datetime.utcnow() - timedelta(days=7)
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
            "assessoria": c.assessoria.razao_social if c.assessoria else None
        })
    return resultados

@router.get("/pdf/corretor/{usuario_id}")
async def pdf_corretor(usuario_id: int, db: Session = Depends(get_db)):
    sete_dias_atras = datetime.utcnow() - timedelta(days=7)

    # JOIN seguro e legível
    comissoes = (
        db.query(Comissao)
          .join(Comissao.apolice)        # join Apolice
          .join(Apolice.proposta)        # join Proposta
          .filter(
              Comissao.corretor_id == usuario_id,
              Comissao.status_pagamento_corretor == "pendente",
              Proposta.data_criacao >= sete_dias_atras
          )
          .all()
    )

    if not comissoes:
        raise HTTPException(status_code=404, detail="Nenhuma comissão pendente nos últimos 7 dias")

    # Monta dados para o template conforme seu HTML
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

    # gera PDF em arquivo temporário e retorna como FileResponse
    tmpdir = tempfile.gettempdir()
    output_path = Path(tmpdir) / f"comissao_corretor_{usuario_id}_{int(datetime.utcnow().timestamp())}.pdf"
    await gerar_pdf(html, str(output_path))

    return FileResponse(str(output_path), filename=f"comissao_{usuario_id}.pdf", media_type="application/pdf")

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
