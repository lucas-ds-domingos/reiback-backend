from fastapi import APIRouter, UploadFile, File, Form, Depends
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

    for key, file_list in arquivos.items():
        if file_list:
            urls[key] = []
            for file in file_list:
                content = await file.read()
                # Gerar nome único: key + tomador + user + timestamp + UUID + filename sanitizado
                unique_name = f"{key}_{tomador_id}_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}_{sanitize_filename(file.filename)}"

                try:
                    bucket.upload(unique_name, content)
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/pdfs/{unique_name}"
                    urls[key].append(public_url)
                except Exception as e:
                    print(f"Erro ao enviar {key}: {str(e)}")

    # Salvar no banco
    doc = DocumentosTomador(
        tomador_id=tomador_id,
        user_id=user_id,
        **urls  # campos do banco devem ser compatíveis com listas ou serializados
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"documentos": urls, "id": doc.id}

@router.get("/api/documentos/list")
def listar_documentos(db: Session = Depends(get_db)):
    documentos = db.query(DocumentosTomador).order_by(DocumentosTomador.data_upload.desc()).all()

    resultado = []
    for doc in documentos:
        tomador = db.query(Tomador).filter(Tomador.id == doc.tomador_id).first()
        user = db.query(Usuario).filter(Usuario.id == doc.user_id).first()

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
                "contrato_social": doc.contrato_social,
                "ultimas_alteracoes": doc.ultimas_alteracoes,
                "balanco": doc.balanco,
                "ultimas_alteracoes_adicional": doc.ultimas_alteracoes_adicional,
                "dre": doc.dre,
                "balancete": doc.balancete,
            },
            "status": doc.status,
            "data_upload": doc.data_upload,
        })

    return resultado
