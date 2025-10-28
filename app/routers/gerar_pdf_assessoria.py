from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import base64
import asyncio
from .gerarPdfComisao import gerar_pdf  # usa sua função original
from datetime import datetime
import os

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

def preparar_html_assessoria(dados, numero_demonstrativo, dados_assessoria):
    template = env.get_template("comisaoAssesoria.html")

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
        logo_base64=logo_base64,
        **dados_assessoria  # envia variáveis como nome, cnpj, endereço etc
    )

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Comissão Assessoria</title>
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


async def gerar_pdf_assessoria(dados, dados_assessoria, output_path="comissao_assessoria.pdf"):
    numero_demonstrativo = f"A-{dados_assessoria.get('id', 0)}-{datetime.now().strftime('%d%m%Y')}"
    html_content = preparar_html_assessoria(dados, numero_demonstrativo, dados_assessoria)
    await gerar_pdf(html_content, output_path)
    return output_path
