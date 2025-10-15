from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import DocumentosTomador, Tomador, Usuario
from supabase import create_client
from dotenv import load_dotenv
from typing import List, Optional
import os
import re
import unicodedata
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation

load_dotenv()

SUPABASE_URL = "https://surlbofnknvgmloladqf.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

def sanitize_filename(filename: str) -> str:
    """
    Remove acentos, espaços e caracteres inválidos para Supabase Storage.
    """
    nfkd_form = unicodedata.normalize('NFKD', filename)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('ASCII')
    sanitized = re.sub(r'[^a-zA-Z0-9_.-]', '_', only_ascii)
    return sanitized

@router.post("/api/documentos")
async def upload_documentos(
    tomador_id: int = Form(...),
    user_id: int = Form(...),
    valor: str = Form(...),
    contrato_social: Optional[List[UploadFile]] = File(None),
    ultimas_alteracoes: Optional[List[UploadFile]] = File(None),
    balanco: Optional[List[UploadFile]] = File(None),
    ultimas_alteracoes_ad: Optional[List[UploadFile]] = File(None),
    dre: Optional[List[UploadFile]] = File(None),
    balancete: Optional[List[UploadFile]] = File(None),
    db: Session = Depends(get_db),
):
    bucket = supabase.storage.from_("pdfs")

    arquivos = {
        "contrato_social": contrato_social,
        "ultimas_alteracoes": ultimas_alteracoes,
        "balanco": balanco,
        "ultimas_alteracoes_adicional": ultimas_alteracoes_ad,
        "dre": dre,
        "balancete": balancete,
    }

    urls = {}

    # Upload arquivos para Supabase
    for key, file_list in arquivos.items():
        if file_list:
            urls[key] = []
            for file in file_list:
                content = await file.read()
                unique_name = f"{key}_{tomador_id}_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}_{sanitize_filename(file.filename)}"
                try:
                    bucket.upload(unique_name, content)
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/pdfs/{unique_name}"
                    urls[key].append(public_url)
                except Exception as e:
                    print(f"Erro ao enviar {key}: {str(e)}")

    # Converter valor para Decimal corretamente
    try:
        if "," in valor:
            # Exemplo: "1.234,56" → "1234.56"
            valor_decimal = Decimal(valor.replace(".", "").replace(",", "."))
        else:
            # Já está no formato "1234.56"
            valor_decimal = Decimal(valor)
    except Exception:
        valor_decimal = Decimal("0.00")


    # Salvar no banco
    doc = DocumentosTomador(
        tomador_id=tomador_id,
        user_id=user_id,
        valor=valor_decimal,
        **urls  # PDFs
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"documentos": urls, "id": doc.id}

SIGNED_URL_EXPIRE = 350  # tempo em segundos que o link será válido

@router.get("/api/documentos/list")
def listar_documentos(db: Session = Depends(get_db)):
    documentos = db.query(DocumentosTomador).order_by(DocumentosTomador.data_upload.desc()).all()
    bucket = supabase.storage.from_("pdfs")

    resultado = []
    for doc in documentos:
        tomador = db.query(Tomador).filter(Tomador.id == doc.tomador_id).first()
        user = db.query(Usuario).filter(Usuario.id == doc.user_id).first()

        # Função auxiliar para gerar URLs assinadas
        def signed_urls(files):
            if not files:
                return None
            urls = []
            for f in files:
                try:
                    url = bucket.create_signed_url(f, SIGNED_URL_EXPIRE)
                    urls.append(url['signedURL'])
                except Exception as e:
                    print("Erro ao gerar signed URL:", e)
            return urls

        resultado.append({
            "id": doc.id,
            "tomador": {
                "id": tomador.id,
                "nome": tomador.nome,
                "cnpj": tomador.cnpj,
            } if tomador else None,
            "usuario": {
                "id": user.id,
                "nome": user.nome,
                "email": user.email,
            } if user else None,
            "documentos": {
                "contrato_social": signed_urls(doc.contrato_social),
                "ultimas_alteracoes": signed_urls(doc.ultimas_alteracoes),
                "balanco": signed_urls(doc.balanco),
                "ultimas_alteracoes_adicional": signed_urls(doc.ultimas_alteracoes_adicional),
                "dre": signed_urls(doc.dre),
                "balancete": signed_urls(doc.balancete),
            },
            "valor": str(doc.valor),
            "status": doc.status,
            "data_upload": doc.data_upload,
        })

    return resultado