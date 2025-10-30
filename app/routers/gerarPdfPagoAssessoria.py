# app/pdf/gerar_pdf.py
import asyncio
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import base64
from playwright.async_api import async_playwright
import os
from datetime import datetime

BROWSERLESS_URL = os.environ.get("BROWSER_WS_ENDPOINT")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Função para formatação de datas
def formatar_data(data):
    if isinstance(data, datetime):
        return data.strftime("%d/%m/%Y")
    return str(data)

# Environment do Jinja
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

# Registrando o filtro
env.filters['formatar_data'] = formatar_data

# --- Função para preparar HTML ---
def preparar_htmlPago(dados: dict, numero_demonstrativo: str, tipo: str = "assessoria", dados_assessoria: dict = None) -> str:
    template_name = "comisaoPagaAssessoria.html" if tipo == "assessoria" else "comisaoPagaCorretor.html"
    template = env.get_template(template_name)

    # Logo base64
    try:
        with open(STATIC_DIR / "images" / "Logo3.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
    except:
        logo_base64 = ""

    # CSS inline
    try:
        with open(STATIC_DIR / "css" / "comisao.css", "r", encoding="utf-8") as f:
            css_content = f.read()
    except:
        css_content = ""

    body_html = template.render(
        dados_por_dia=dados.get("dados_por_dia", dados),
        nome_assessoria=dados_assessoria.get("nome_assessoria", "") if dados_assessoria else "",
        cnpj=dados_assessoria.get("cnpj", "") if dados_assessoria else "",
        endereco=dados_assessoria.get("endereco", "") if dados_assessoria else "",
        cidade=dados_assessoria.get("cidade", "") if dados_assessoria else "",
        uf=dados_assessoria.get("uf", "") if dados_assessoria else "",
        cep=dados_assessoria.get("cep", "") if dados_assessoria else "",
        email=dados_assessoria.get("email", "") if dados_assessoria else "",
        corretor_nome="",  # vazio para assessoria
        numeroDemonstrativo=numero_demonstrativo,
        logo_base64=logo_base64
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Comissão</title>
            <style>
                *, *::before, *::after {{ box-sizing: border-box; }}
                body {{ margin: 0; padding: 20px; font-family: Arial, sans-serif; font-size: 12px; color: #333; background-color: #fff; }}
                {css_content}
            </style>
        </head>
        <body>
            {body_html}
        </body>
    </html>
    """
    return html_content

# --- Função para gerar PDF ---
async def gerar_pdfPago(html_content: str, output_path="comissao.pdf") -> str:
    async with async_playwright() as p:
        if BROWSERLESS_URL:
            browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL)
        else:
            browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(path=output_path, format="A4", print_background=True)

        await browser.close()
    return output_path



# Função auxiliar para converter datas para exibição no template
def formatar_data(data: datetime) -> str:
    return data.strftime("%d/%m/%Y") if isinstance(data, datetime) else str(data)
