# app/routers/comissoes.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from ..gerarPdfComisao import preparar_html, gerar_pdf
from ...database import get_db
from ...models import Comissao

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
    comissoes = db.query(Comissao).filter(
        Comissao.corretor_id == usuario_id,
        Comissao.status_pagamento_corretor == "pendente",
        Comissao.apolice.has(Comissao.apolice.proposta.has(Comissao.apolice.proposta.data_criacao >= datetime.utcnow() - timedelta(days=7)))
    ).all()
    dados = [{
        "numero_apolice": c.apolice.numero,
        "tomador_nome": c.apolice.proposta.tomador.nome,
        "segurado_nome": c.apolice.proposta.segurado.nome,
        "premio": float(c.valor_premio),
        "percentual": float(c.percentual_corretor),
        "comissao_valor": float(c.valor_corretor)
    } for c in comissoes]
    numero_demonstrativo = f"{datetime.utcnow().strftime('%d/%m/%Y')}-{usuario_id}"
    html = preparar_html(dados, numero_demonstrativo)
    output_path = f"pdfs/comissao_corretor_{usuario_id}.pdf"
    await gerar_pdf(html, output_path)
    return {"pdf_path": output_path}

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
