# app/pdf/gerar_pdf.py
import asyncio
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import base64
from playwright.async_api import async_playwright
import os


BROWSERLESS_URL = os.environ.get("BROWSER_WS_ENDPOINT")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

def preparar_html(dados, numero_demonstrativo):
    template = env.get_template("comisaoCorretor.html")
    # Logo base64
    try:
        with open(STATIC_DIR / "images" / "logo3.png", "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
    except:
        logo_base64 = ""
    # CSS inline
    css_path = STATIC_DIR / "css" / "comisao.css"
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
    except:
        css_content = ""
    body_html = template.render(
        dados=dados,
        numeroDesmontrativo=numero_demonstrativo,
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

async def gerar_pdf(html_content: str, output_path="comissao.pdf"):
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL)
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(path=output_path, format="A4", print_background=True)
        await browser.close()
    return output_path
