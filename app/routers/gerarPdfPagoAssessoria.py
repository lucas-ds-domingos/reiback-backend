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
def preparar_htmlPago(dados, dados_assessoria=None):
    """
    Gera o HTML para o PDF de comissões pagas de uma assessoria.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(base_dir, "../templates")

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html", "xml"])
    )

    # 🔹 Adiciona filtro customizado para formatar data
    def formatar_data(value):
        if not value:
            return ""
        try:
            return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
        except Exception:
            return str(value)

    env.filters["formatar_data"] = formatar_data

    template = env.get_template("comisaoPagaAssessoria.html")

    html_content = template.render(
        dados=dados,
        dados_assessoria=dados_assessoria  # 🔹 Agora o template recebe os dados da assessoria
    )

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
