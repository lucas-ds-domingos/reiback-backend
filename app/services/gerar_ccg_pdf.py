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
template = env.get_template("ccg.html")


async def gerar_pdf_ccg(data: dict) -> bytes:
    """Gera PDF da CCG com fundo e renderização dinâmica de fiadores e representantes"""
    html = montar_html_ccg(data)

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL)
        page = await browser.new_page()
        await page.set_content(html, wait_until="networkidle")
        pdf_bytes = await page.pdf(format="A4", print_background=True)
        await browser.close()
    output_pdf = Path(__file__).parent / "ccg_teste.pdf"
    output_pdf.write_bytes(pdf_bytes) 
    return pdf_bytes


def montar_html_ccg(data: dict) -> str:
    """Monta HTML da CCG com fundo e renderização dinâmica"""

    # Carrega CSS
    css_path = static_path / "css" / "proposta.css"
    with open(css_path, "r", encoding="utf-8") as f:
        css_content = f.read()

    # Carrega imagem de fundo
    fundo_path = static_path / "images" / "teste.jpeg"
    with open(fundo_path, "rb") as f:
        fundo_b64 = base64.b64encode(f.read()).decode()

    # Dados dinâmicos (fiadores e representantes podem ser listas)
    pdf_data = {
        "tomador": data.get("tomador"),
        "fiadores": data.get("fiadores", []),
        "representantes_legais": data.get("representantes_legais", []),
    }

    body_html = template.render(**pdf_data)

    return f"""
    <html>
        <head>
            <meta charset="utf-8">
            <style>
            .page {{
                size: A4;
                background: url("data:image/jpeg;base64,{fundo_b64}") no-repeat center top;
                background-size: cover;
                page-break-after: always;
            }}
            {css_content}
            </style>
        </head>
        <body>
            {body_html}
        </body>
    </html>
    """
