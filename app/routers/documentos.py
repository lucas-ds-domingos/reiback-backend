from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from ..database import get_db  # sua função de conexão com o DB
from ..models import DocumentosTomador  # sua tabela
from supabase import create_client
from dotenv import load_dotenv
import shutil
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
    contrato_social: UploadFile | None = File(None),
    ultimas_alteracoes: UploadFile | None = File(None),
    balanco: UploadFile | None = File(None),
    ultimas_alteracoes_ad: UploadFile | None = File(None),
    dre: UploadFile | None = File(None),
    balancete: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    bucket = supabase.storage.from_("pdfs")

    arquivos = {
        "contrato_social": contrato_social,
        "ultimas_alteracoes": ultimas_alteracoes,
        "balanco": balanco,
        "ultimas_alteracoes_adicional": ultimas_alteracoes_ad,  # corrigido
        "dre": dre,
        "balancete": balancete,
    }

    urls = {}

    for key, file in arquivos.items():
        if file:
            file_content = await file.read()  # lê direto o conteúdo
            unique_name = f"{key}_{tomador_id}_{user_id}_{file.filename}"

            try:
                bucket.upload(unique_name, file_content)
                public_url = f"{SUPABASE_URL}/storage/v1/object/public/pdfs/{unique_name}"
                urls[key] = public_url
            except Exception as e:
                print(f"Erro ao enviar {key}: {str(e)}")

    # --- Salvar no banco ---
    doc = DocumentosTomador(
        tomador_id=tomador_id,
        user_id=user_id,
        **urls
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"documentos": urls, "id": doc.id}
