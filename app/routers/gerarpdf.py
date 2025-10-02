from fastapi import APIRouter, Response, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
from ..database import get_db
from ..models import Proposta
from jinja2 import Environment, FileSystemLoader, select_autoescape
import base64
import traceback
from weasyprint import HTML, CSS

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent  # /app
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml']),
    cache_size=50
)

class PropostaPayload(BaseModel):
    propostaId: int
    textoCompleto: str | None = None

def preparar_html(proposta, texto_completo: str | None) -> str:
    template = env.get_template("proposta.html")

    def format_money(valor):
        return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    pdf_data = {
        "numeroProposta": proposta.numero,
        "inicioVigencia": proposta.inicio_vigencia.strftime("%d/%m/%Y") if proposta.inicio_vigencia else "",
        "terminoVigencia": proposta.termino_vigencia.strftime("%d/%m/%Y") if proposta.termino_vigencia else "",
        "diasVigencia": proposta.dias_vigencia,
        "valor": format_money(proposta.importancia_segurada),
        "premio": format_money(proposta.premio),
        "modalidade": proposta.modalidade,
        "subgrupo": proposta.subgrupo,
        "numero_contrato": proposta.numero_contrato,
        "edital_processo": proposta.edital_processo,
        "percentual": float(proposta.percentual or 0),
        "nomeTomador": proposta.tomador.nome,
        "cnpjTomador": proposta.tomador.cnpj,
        "enderecoTomador": proposta.tomador.endereco or '',
        "ufTomador": f"{proposta.tomador.uf or ''} {proposta.tomador.municipio or ''}".strip(),
        "cepTomador": proposta.tomador.cep or "",
        "nomeBeneficiario": proposta.segurado.nome,
        "cnpjBeneficiario": proposta.segurado.cpf_cnpj,
        "enderecoBeneficiario": f"{proposta.segurado.logradouro or ''}, {proposta.segurado.numero or ''} {proposta.segurado.complemento or ''} - {proposta.segurado.bairro or ''}".strip(),
        "ufBeneficiario": f"{proposta.segurado.municipio or ''}, {proposta.segurado.uf or ''}".strip(),
        "cepBeneficiario": proposta.segurado.cep or "",
        "usuarioNome": proposta.usuario.nome,
        "usuarioEmail": proposta.usuario.email,
        "textoCompleto": texto_completo or proposta.text_modelo or "",
    }

    # CSS
    css_path = STATIC_DIR / "css/proposta.css"
    css_content = ""
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()

    # Imagem de fundo
    fundo_path = STATIC_DIR / "images/teste.jpeg"
    fundo_b64 = ""
    if fundo_path.exists():
        with open(fundo_path, "rb") as f:
            fundo_b64 = base64.b64encode(f.read()).decode()

    body_html = template.render(**pdf_data)

    html_content = f"""
    <html>
        <head>
            <style>
            @page {{ size: A4; margin: 2cm; }}
            .page {{
                page-break-after: always;
                background: url("data:image/jpeg;base64,{fundo_b64}") no-repeat center top;
                background-size: cover;
            }}
            {css_content}
            </style>
        </head>
        <body>
            {body_html}
        </body>
    </html>
    """
    return html_content

@router.post("/", response_class=Response)
async def gerar_pdf_endpoint(payload: PropostaPayload, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == payload.propostaId).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    try:
        html_content = preparar_html(proposta, payload.textoCompleto)
        css_path = STATIC_DIR / "css/proposta.css"
        css = CSS(filename=str(css_path)) if css_path.exists() else None
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css] if css else None)
        print("PDF gerado com WeasyPrint")
    except Exception as e:
        print("Erro ao gerar PDF:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="proposta_{proposta.numero}.pdf"'}
    )
