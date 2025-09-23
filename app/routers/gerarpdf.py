from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import BaseModel
from pathlib import Path
from ..database import get_db
from ..models import Proposta
from playwright.sync_api import sync_playwright
import base64

router = APIRouter()

# Caminhos
current_dir = Path(__file__).parent
templates_path = current_dir.parent / "templates"
static_path = current_dir.parent / "static"

# Jinja2
env = Environment(
    loader=FileSystemLoader(str(templates_path)),
    autoescape=select_autoescape(['html', 'xml']),
    cache_size=50
)
template = env.get_template("proposta.html")


class PropostaPayload(BaseModel):
    propostaId: int
    textoCompleto: str | None = None


def gerar_pdf_playwright(html_content: str) -> bytes:
    """Gera PDF usando Playwright Síncrono."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html_content, wait_until="networkidle")
        pdf_bytes = page.pdf(format="A4", print_background=True)
        browser.close()
        return pdf_bytes


@router.post("/", response_class=Response)
async def gerar_pdf(payload: PropostaPayload, request: Request, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == payload.propostaId).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

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
        "textoCompleto": payload.textoCompleto or proposta.text_modelo or "",
    }

    # Lê o CSS
    css_path = static_path / "css" / "proposta.css"
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Lê a imagem de fundo e converte para base64
    fundo_path = static_path / "images" / "teste.jpeg"
    with open(fundo_path, "rb") as f:
        fundo_b64 = base64.b64encode(f.read()).decode()

    # Renderiza HTML do template
    body_html = template.render(request=request, **pdf_data)

    # Monta HTML completo com CSS e imagem de fundo embutidos
    html_content = f"""
    <html>
        <head>
            <style>
            .page{{
                size: A4;
                background: url("data:image/jpeg;base64,{fundo_b64}") no-repeat center top;
                background-size: cover;
            }},
            .watermark {{ 
                    position: absolute;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%) rotate(-45deg);
                font-size: 60px;
                color: rgba(255, 0, 0, 0.3); /* vermelho com transparência */
                font-weight: bold;
                pointer-events: none; /* não interfere no conteúdo */
                z-index: 1000;
                white-space: nowrap;
                text-transform: uppercase;}}
            {css_content}
            </style>
        </head>
        <body>
            {body_html}
        </body>
    </html>
    """

    # Gera PDF em thread pool para não travar o loop async
    pdf_bytes = await run_in_threadpool(gerar_pdf_playwright, html_content)

    return Response(content=pdf_bytes, media_type="application/pdf")
