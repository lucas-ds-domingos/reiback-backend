# app/pdf/gerar_pdf.py
import os
import base64
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from playwright.async_api import async_playwright

# Se quiser usar browserless em produção, setar a variável BROWSER_WS_ENDPOINT
BROWSERLESS_URL = os.environ.get("BROWSER_WS_ENDPOINT")

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Cria ambiente Jinja
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "xml"])
)

# ===== filtros utilitários =====
def formatar_data(value):
    """
    Entrada pode ser datetime, date, string 'YYYY-MM-DD' ou None.
    Retorna DD/MM/YYYY ou string vazia.
    """
    if not value:
        return ""
    if isinstance(value, (datetime, )):
        return value.strftime("%d/%m/%Y")
    try:
        # tenta tratar strings "YYYY-MM-DD" ou contendo tempo
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value)

def formatar_moeda(value):
    """
    Formata um número em '1.234,56' — retorna string.
    Se inválido, retorna '0,00'.
    """
    try:
        v = float(value)
    except Exception:
        return "0,00"
    # formato com milhares ponto e separador decimal vírgula
    s = f"{v:,.2f}"          # ex: '1,234.56'
    # converter para formato BR: '1.234,56'
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s

# registra filtros no ambiente
env.filters["formatar_data"] = formatar_data
env.filters["formatar_moeda"] = formatar_moeda

# ===== função que prepara o HTML =====
def preparar_htmlPagoCorretor(dados, numero_demonstrativo, tipo: str = "corretor", dados_corretor: dict | None = None):
    """
    Prepara o HTML para o PDF de comissões pagas.
    Parâmetros esperados pela sua rota:
      - dados: dict contendo o mapa dados_por_dia (ex: {'23/10/2025': [ {...}, {...} ]})
      - numero_demonstrativo: string
      - tipo: "assessoria" ou "corretor" (usado para escolher template)
      - dados_assessoria: dict com chaves nome_assessoria, cnpj, endereco, cidade, uf, cep, email
    Retorna: string HTML pronto para gerar o PDF.
    """
    template_name = "comisaoPagaCorretor.html"
    try:
        template = env.get_template(template_name)
    except Exception as e:
        # levantar erro com mensagem clara para logs
        raise RuntimeError(f"Template '{template_name}' não encontrado em {TEMPLATES_DIR}: {e}")

    # carregar logo em base64 (se existir)
    logo_base64 = ""
    try:
        logo_path = STATIC_DIR / "images" / "Logo3.png"
        if logo_path.exists():
            with open(logo_path, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
    except Exception:
        logo_base64 = ""

    # carregar CSS inline (opcional)
    css_content = ""
    try:
        css_path = STATIC_DIR / "css" / "comisao.css"
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
    except Exception:
        css_content = ""

    # garantir que 'dados' tem a forma esperada: dict de listas com campos numéricos.
    # sua rota já monta os objetos com as chaves:
    #   apolice_numero, tomador_nome, segurado_nome, corretor_nome,
    #   valor_premio, percentual_assessoria, valor_assessoria
    dados_por_dia = {}
    # se o usuário forneceu já um dict com chaves de dia -> lista, usa direto
    if isinstance(dados, dict):
        # algumas rotas passaram 'dados' já sendo o dados_por_dia
        dados_por_dia = dados
    else:
        # fallback: tenta tratar de forma segura
        dados_por_dia = {"": []}

    # garantir tipos: converter strings numéricas para float e preencher chaves faltantes
    for dia, lista in list(dados_por_dia.items()):
        safe_list = []
        for item in lista:
            # item pode ser objeto ORM ou dict. Normaliza para dict.
            if not isinstance(item, dict):
                try:
                    # tenta extrair atributos
                    item = {
                        "apolice_numero": getattr(item, "apolice_numero", "") or "",
                        "tomador_nome": getattr(item, "tomador_nome", "") or "",
                        "segurado_nome": getattr(item, "segurado_nome", "") or "",
                        "corretor_nome": getattr(item, "corretor_nome", "") or "",
                        "valor_premio": float(getattr(item, "valor_premio", 0) or 0),
                        "percentual_corretor": float(getattr(item, "percentual_corretor", 0) or 0),
                        "valor_corretor": float(getattr(item, "valor_corretor", 0) or 0),
                    }
                except Exception:
                    item = {}
            # garantir chaves e tipos
            safe = {
                "apolice_numero": item.get("apolice_numero", "") if isinstance(item, dict) else "",
                "tomador_nome": item.get("tomador_nome", "") if isinstance(item, dict) else "",
                "segurado_nome": item.get("segurado_nome", "") if isinstance(item, dict) else "",
                "corretor_nome": item.get("corretor_nome", "") if isinstance(item, dict) else "",
                "valor_premio": float(item.get("valor_premio", 0) or 0),
                "percentual_corretor": float(item.get("percentual_corretor", 0) or 0),
                # nome da chave usada no template final: valor_assessoria
                "valor_corretor": float(item.get("valor_corretor", item.get("comissao_valor", 0) or 0)),
            }
            safe_list.append(safe)
        dados_por_dia[dia] = safe_list

    # montar contexto para o template usando exatamente as variáveis que o seu HTML espera
    ctx = {
        "dados_por_dia": dados_por_dia,
        "numeroDemonstrativo": numero_demonstrativo,
        "logo_base64": logo_base64,
        # preencher campos da assessoria (nome_assessoria, cnpj, endereco, cidade, uf, cep, email)
        "nome_assessoria": (dados_corretor.get("nome_assessoria") if dados_corretor else ""),
        "cnpj": (dados_corretor.get("cnpj") if dados_corretor else ""),
        "endereco": (dados_corretor.get("endereco") if dados_corretor else ""),
        "cidade": (dados_corretor.get("cidade") if dados_corretor else ""),
        "uf": (dados_corretor.get("uf") if dados_corretor else ""),
        "cep": (dados_corretor.get("cep") if dados_corretor else ""),
        "email": (dados_corretor.get("email") if dados_corretor else ""),
        "base_path": "/static",  # caso seu template espere base_path para css
    }

    # renderiza
    body_html = template.render(**ctx)

    # monta HTML final (inline CSS)
    html_content = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Comissões Pagas</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; }}
    body {{ margin:0; padding:20px; font-family: Arial,Helvetica,sans-serif; font-size:12px; color:#333; background:#fff; }}
    {css_content}
  </style>
</head>
<body>
{body_html}
</body>
</html>"""
    return html_content

# ===== função que gera o PDF =====
async def gerar_pdfPagoCorretor(html_content: str, output_path="comissao.pdf") -> str:
    """
    Gera o PDF a partir do HTML.
    Usa Browserless (CDP) se BROWSERLESS_URL configurada; senão abre Chromium local.
    """
    # Playwright: conectar ao browserless se variável estiver setada
    async with async_playwright() as p:
        if BROWSERLESS_URL:
            # conectar ao browserless / chromium remoto via CDP
            browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL)
        else:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])

        page = await browser.new_page()
        # setar conteúdo
        await page.set_content(html_content, wait_until="networkidle")
        # gerar pdf
        await page.pdf(path=str(output_path), format="A4", print_background=True)
        await browser.close()

    return str(output_path)
