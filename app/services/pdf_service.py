from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import base64
import os
from playwright.async_api import async_playwright

BROWSERLESS_URL = os.environ.get("BROWSER_WS_ENDPOINT")

current_dir = Path(__file__).parent.parent
templates_path = current_dir / "templates"
static_path = current_dir / "static"

env = Environment(
    loader=FileSystemLoader(str(templates_path)),
    autoescape=select_autoescape(["html", "xml"])
)
template = env.get_template("apolice.html")


async def gerar_pdf_playwright(html_content: str) -> bytes:
    """Gera PDF usando Browserless remoto."""
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        pdf_bytes = await page.pdf(format="A4", print_background=True)
        await browser.close()
        return pdf_bytes


def montar_html_apolice(proposta, textoCompleto: str | None = None) -> str:
    def format_money(valor):
        return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    pdf_data = {
        "numeroProposta": f"FIN-{proposta.id:05d}",
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
        "textoCompleto": textoCompleto or proposta.text_modelo or "",
    }

    # CSS + imagem de fundo
    css_path = static_path / "css" / "proposta.css"
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    fundo_path = static_path / "images" / "teste.jpeg"
    with open(fundo_path, "rb") as f:
        fundo_b64 = base64.b64encode(f.read()).decode()

    ass_path = static_path / "images" / "assinatura.jpg"
    with open(ass_path, "rb") as f:
        ass_b64 = base64.b64encode(f.read()).decode()

    pdf_data["assinatura_base64"] = ass_b64
    body_html = template.render(**pdf_data)

    return f"""
    <html>
        <head>
            <style>
            .page{{
                size: A4;
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
