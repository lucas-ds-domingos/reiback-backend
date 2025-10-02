from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from pathlib import Path
import io
import base64
import traceback
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML, CSS
from ..database import get_db
from ..models import Proposta

router = APIRouter()

# Paths absolutos (funciona em local e container/Docker)
BASE_DIR = Path(__file__).resolve().parent.parent  # Raiz do app (ex: /app)
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# Config Jinja2
env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(['html', 'xml']),
    cache_size=50  # Cache pequeno para dev
)

class PropostaPayload(BaseModel):
    propostaId: int
    textoCompleto: str | None = None

def preparar_html(proposta, texto_completo: str | None) -> str:
    # Carrega template
    try:
        template = env.get_template("proposta.html")
    except Exception as e:
        raise ValueError(f"Erro ao carregar template proposta.html: {e}")

    def format_money(valor):
        # Formatação BR para dinheiro (fallback se locale não disponível)
        try:
            return f"R$ {float(valor or 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except:
            return f"R$ {valor or 0}"

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
        "nomeTomador": getattr(proposta.tomador, 'nome', ''),
        "cnpjTomador": getattr(proposta.tomador, 'cnpj', ''),
        "enderecoTomador": getattr(proposta.tomador, 'endereco', ''),
        "ufTomador": f"{getattr(proposta.tomador, 'uf', '')} {getattr(proposta.tomador, 'municipio', '')}".strip(),
        "cepTomador": getattr(proposta.tomador, 'cep', ''),
        "nomeBeneficiario": getattr(proposta.segurado, 'nome', ''),
        "cnpjBeneficiario": getattr(proposta.segurado, 'cpf_cnpj', ''),
        "enderecoBeneficiario": f"{getattr(proposta.segurado, 'logradouro', '')}, {getattr(proposta.segurado, 'numero', '')} {getattr(proposta.segurado, 'complemento', '')} - {getattr(proposta.segurado, 'bairro', '')}".strip(),
        "ufBeneficiario": f"{getattr(proposta.segurado, 'municipio', '')}, {getattr(proposta.segurado, 'uf', '')}".strip(),
        "cepBeneficiario": getattr(proposta.segurado, 'cep', ''),
        "usuarioNome": getattr(proposta.usuario, 'nome', ''),
        "usuarioEmail": getattr(proposta.usuario, 'email', ''),
        "textoCompleto": texto_completo or getattr(proposta, 'text_modelo', ''),
    }

    # Carrega CSS como string (fallback vazio se não existir)
    css_content = ""
    css_path = STATIC_DIR / "css/proposta.css"
    if css_path.exists():
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
        except Exception as e:
            print(f"Erro ao carregar CSS: {e}")

    # Carrega imagem de fundo como base64 (fallback vazio se não existir)
    fundo_b64 = ""
    fundo_path = STATIC_DIR / "images/teste.jpeg"
    if fundo_path.exists():
        try:
            with open(fundo_path, "rb") as f:
                fundo_b64 = base64.b64encode(f.read()).decode()
        except Exception as e:
            print(f"Erro ao carregar imagem de fundo: {e}")

    # Renderiza o body do template
    body_html = template.render(**pdf_data)

    # Monta HTML completo com CSS e background inline
    html_content = f"""
    <!DOCTYPE html>
    <html>
        <head>
            <meta charset="utf-8">
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: Arial, sans-serif; }}
                .page {{ page-break-after: always; }}
                .background {{ 
                    background: url("data:image/jpeg;base64,{fundo_b64}") no-repeat center top; 
                    background-size: cover; 
                }}
                {css_content}
            </style>
        </head>
        <body class="background">
            {body_html}
        </body>
    </html>
    """
    return html_content

@router.post("/", response_class=StreamingResponse)
async def gerar_pdf_endpoint(payload: PropostaPayload, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == payload.propostaId).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    try:
        html_content = preparar_html(proposta, payload.textoCompleto)
        
        # Cria CSS object (se content vazio, usa None)
        css_content = ""
        css_path = STATIC_DIR / "css/proposta.css"
        if css_path.exists():
            with open(css_path, "r", encoding="utf-8") as f:
                css_content = f.read()
        css = CSS(string=css_content) if css_content else None
        
        # Gera PDF com WeasyPrint
        pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css] if css else None)
        print("PDF gerado com WeasyPrint com sucesso")
        
    except Exception as e:
        print("Erro ao gerar PDF:", str(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao gerar PDF: {str(e)}")

    # Buffer para streaming
    buffer = io.BytesIO(pdf_bytes)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="proposta_{proposta.numero}.pdf"',
            "Content-Length": str(len(pdf_bytes))
        }
    )
