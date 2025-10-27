import asyncio
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import base64
from playwright.async_api import async_playwright

# ---------------------------
# Configurações de paths
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

# ---------------------------
# Dados fictícios
# ---------------------------
dados = [
    {
        "numero_apolice": "12345",
        "tomador_nome": "Empresa Exemplo LTDA",
        "segurado_nome": "João da Silva",
        "premio": 1500.50,
        "percentual": 20,
        "comissao_valor": 300.10,
    },
    {
        "numero_apolice": "12346",
        "tomador_nome": "Outra Empresa SA",
        "segurado_nome": "Maria Oliveira",
        "premio": 2500.75,
        "percentual": 15,
        "comissao_valor": 375.11,
    },
]

numero_demonstrativo = "001/2025"

# ---------------------------
# Função de gerar PDF
# ---------------------------
async def gerar_pdf(html_content: str, output_path="comissao_teste.pdf"):
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="networkidle")
        await page.pdf(path=output_path, format="A4", print_background=True)
        await browser.close()
    print(f"PDF gerado em: {output_path}")

# ---------------------------
# Preparar HTML
# ---------------------------
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
    except Exception as e:
        print(f"Erro ao ler CSS: {e}")
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

# ---------------------------
# Main
# ---------------------------
def main():
    html = preparar_html(dados, numero_demonstrativo)
    asyncio.run(gerar_pdf(html))

if __name__ == "__main__":
    main()
