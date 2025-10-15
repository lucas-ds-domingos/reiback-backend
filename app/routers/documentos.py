from fastapi import APIRouter, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import get_db  # sua função de conexão com o DB
from models import DocumentosTomador  # sua tabela
from supabase import create_client
from dotenv import load_dotenv
import shutil
import os


load_dotenv()

SUPABASE_URL = "https://surlbofnknvgmloladqf.supabase.co"
SUPABASE_KEY = os.getenv("sua_service_role_key")
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
    arquivos = {
        "contrato_social": contrato_social,
        "ultimas_alteracoes": ultimas_alteracoes,
        "balanco": balanco,
        "ultimas_alteracoes_adicional": ultimas_alteracoes_ad,
        "dre": dre,
        "balancete": balancete,
    }

    urls = {}

    for key, file in arquivos.items():
        if file:
            local_path = f"temp_{file.filename}"
            with open(local_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Upload para Supabase
            bucket = supabase.storage.from_("pdfs")
            bucket.upload(file.filename, open(local_path, "rb"))
            url = bucket.get_public_url(file.filename)["publicUrl"]
            urls[key] = url

            os.remove(local_path)

    # Salvar no banco
    doc = DocumentosTomador(
        tomador_id=tomador_id,
        user_id=user_id,
        **urls  # atribui os campos dinamicamente
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"documentos": urls, "id": doc.id}
