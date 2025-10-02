from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from pydantic import BaseModel
import io

router = APIRouter()

class PropostaPayload(BaseModel):
    propostaId: int
    textoCompleto: str | None = None

def gerar_pdf(dados: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []

    styles = getSampleStyleSheet()
    style_normal = styles["Normal"]
    style_title = styles["Title"]

    # Título
    story.append(Paragraph("📄 Proposta de Seguro", style_title))
    story.append(Spacer(1, 20))

    # Dados em tabela
    tabela_dados = []
    for chave, valor in dados.items():
        tabela_dados.append([Paragraph(f"<b>{chave}</b>", style_normal), Paragraph(str(valor), style_normal)])

    tabela = Table(tabela_dados, colWidths=[150, 350])
    tabela.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(tabela)

    story.append(Spacer(1, 20))

    if "textoCompleto" in dados and dados["textoCompleto"]:
        story.append(Paragraph("<b>Texto Completo:</b>", style_normal))
        story.append(Paragraph(dados["textoCompleto"], style_normal))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

@router.post("/", response_class=StreamingResponse)
async def gerar_pdf_endpoint(payload: PropostaPayload, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == payload.propostaId).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    dados = {
        "Número da Proposta": proposta.numero,
        "Início Vigência": proposta.inicio_vigencia.strftime("%d/%m/%Y") if proposta.inicio_vigencia else "",
        "Término Vigência": proposta.termino_vigencia.strftime("%d/%m/%Y") if proposta.termino_vigencia else "",
        "Dias Vigência": proposta.dias_vigencia,
        "Valor": proposta.importancia_segurada,
        "Prêmio": proposta.premio,
        "Modalidade": proposta.modalidade,
        "Subgrupo": proposta.subgrupo,
        "Contrato": proposta.numero_contrato,
        "Edital Processo": proposta.edital_processo,
        "Percentual": proposta.percentual,
        "Tomador": proposta.tomador.nome if proposta.tomador else "",
        "CNPJ Tomador": proposta.tomador.cnpj if proposta.tomador else "",
        "Segurado": proposta.segurado.nome if proposta.segurado else "",
        "CNPJ Segurado": proposta.segurado.cpf_cnpj if proposta.segurado else "",
        "Usuário": proposta.usuario.nome if proposta.usuario else "",
        "E-mail Usuário": proposta.usuario.email if proposta.usuario else "",
        "textoCompleto": payload.textoCompleto or proposta.text_modelo or "",
    }

    pdf_bytes = gerar_pdf(dados)
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=proposta_{proposta.numero}.pdf"}
    )
