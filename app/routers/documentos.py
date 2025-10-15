from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import DocumentosTomador
from supabase import create_client
from dotenv import load_dotenv
from typing import List, Optional
import os

load_dotenv()

SUPABASE_URL = "https://surlbofnknvgmloladqf.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

router = APIRouter()

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

    # Inicializa todos os campos como listas vazias
    urls = {
        "contrato_social": [],
        "ultimas_alteracoes": [],
        "balanco": [],
        "ultimas_alteracoes_adicional": [],
        "dre": [],
        "balancete": [],
    }

    arquivos = {
        "contrato_social": contrato_social,
        "ultimas_alteracoes": ultimas_alteracoes,
        "balanco": balanco,
        "ultimas_alteracoes_adicional": ultimas_alteracoes_ad,
        "dre": dre,
        "balancete": balancete,
    }

    # Upload de arquivos para Supabase
    for key, file_list in arquivos.items():
        if file_list:
            for file in file_list:
                content = await file.read()
                unique_name = f"{key}_{tomador_id}_{user_id}_{file.filename}"
                try:
                    bucket.upload(unique_name, content)
                    public_url = f"{SUPABASE_URL}/storage/v1/object/public/pdfs/{unique_name}"
                    urls[key].append(public_url)
                except Exception as e:
                    print(f"Erro ao enviar {key} ({file.filename}): {str(e)}")

    # Converte listas vazias em None antes de salvar no banco
    doc = DocumentosTomador(
        tomador_id=tomador_id,
        user_id=user_id,
        contrato_social=urls["contrato_social"] or None,
        ultimas_alteracoes=urls["ultimas_alteracoes"] or None,
        balanco=urls["balanco"] or None,
        ultimas_alteracoes_adicional=urls["ultimas_alteracoes_adicional"] or None,
        dre=urls["dre"] or None,
        balancete=urls["balancete"] or None
    )

    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"documentos": urls, "id": doc.id}
