# app/routers/gerarPdfPagoAssessoria.py
import base64
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from datetime import datetime
from playwright.async_api import async_playwright
import os

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# ======================
# 🔹 Filtro para formatar data usado no template
# ======================
def formatar_data(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value)

# Cria ambiente Jinja e registra o filtro
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)
env.filters["formatar_data"] = formatar_data  # <-- AQUI RESOLVE O ERRO

# ======================
# Restante do seu código igual
# ======================
def preparar_htmlPago(dados: dict, numero_demonstrativo: str, tipo: str = "assessoria") -> str:
    template_name = "comisaoPagaAssessoria.html" if tipo == "assessoria" else "comisaoPagaCorretor.html"
    template = env.get_template(template_name)

    try:
        with open(STATIC_DIR / "images" / "Logo3.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
    except:
        logo_base64 = ""

    try:
        with open(STATIC_DIR / "css" / "comisao.css", "r", encoding="utf-8") as f:
            css_content = f.read()
    except:
        css_content = ""

    body_html = template.render(
        dados_por_dia=dados.get("dados_por_dia", {}),
        nome_assessoria=dados.get("nome_assessoria", ""),
        cnpj=dados.get("cnpj", ""),
        endereco=dados.get("endereco", ""),
        cidade=dados.get("cidade", ""),
        uf=dados.get("uf", ""),
        cep=dados.get("cep", ""),
        email=dados.get("email", ""),
        numeroDemonstrativo=numero_demonstrativo,
        logo_base64=logo_base64
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <style>{css_content}</style>
    </head>
    <body>{body_html}</body>
    </html>
    """
    return html_content


async def gerar_pdfPago(html_content: str, output_path="comissao.pdf") -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(path=output_path, format="A4", print_background=True)
        await browser.close()
    return output_path




# Função auxiliar para converter datas para exibição no template
def formatar_data(data: datetime) -> str:
    return data.strftime("%d/%m/%Y") if isinstance(data, datetime) else str(data)
