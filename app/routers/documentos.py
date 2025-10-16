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

SIGNED_URL_EXPIRE = 360  # 6 minutos de validade

def sanitize_filename(filename: str) -> str:
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

    paths = {}  # salvamos apenas o nome do arquivo no bucket

    # Upload arquivos para Supabase
    for key, file_list in arquivos.items():
        if file_list:
            paths[key] = []
            for file in file_list:
                content = await file.read()
                unique_name = f"{key}_{tomador_id}_{user_id}_{int(datetime.now().timestamp())}_{uuid.uuid4().hex}_{sanitize_filename(file.filename)}"
                try:
                    bucket.upload(unique_name, content, {"content-type": "application/pdf"})
                    paths[key].append(unique_name)  # armazenamos somente o path
                except Exception as e:
                    print(f"Erro ao enviar {key}: {str(e)}")

    # Converter valor para Decimal
    try:
        if "," in valor:
            valor_decimal = Decimal(valor.replace(".", "").replace(",", "."))
        else:
            valor_decimal = Decimal(valor)
    except Exception:
        valor_decimal = Decimal("0.00")

    # Salvar no banco
    doc = DocumentosTomador(
        tomador_id=tomador_id,
        user_id=user_id,
        valor=valor_decimal,
        **paths
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {"message": "Arquivos enviados com sucesso", "id": doc.id}


@router.get("/api/documentos/list")
def listar_documentos(db: Session = Depends(get_db)):
    documentos = db.query(DocumentosTomador).filter(DocumentosTomador.status=='pendente').order_by(DocumentosTomador.data_upload.desc()).all()
    bucket = supabase.storage.from_("pdfs")

    def generate_signed_urls(files):
        if not files:
            return []
        urls = []
        for f in files:
            try:
                signed = bucket.create_signed_url(f, SIGNED_URL_EXPIRE)
                urls.append(signed['signedURL'])
            except Exception as e:
                print("Erro ao gerar signed URL:", e)
        return urls

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
                "contrato_social": generate_signed_urls(doc.contrato_social),
                "ultimas_alteracoes": generate_signed_urls(doc.ultimas_alteracoes),
                "balanco": generate_signed_urls(doc.balanco),
                "ultimas_alteracoes_adicional": generate_signed_urls(doc.ultimas_alteracoes_adicional),
                "dre": generate_signed_urls(doc.dre),
                "balancete": generate_signed_urls(doc.balancete),
            },
            "valor": str(doc.valor),
            "status": doc.status,
            "data_upload": doc.data_upload,
        })

    return resultado


@router.patch("/api/documentos/{doc_id}/status")
def atualizar_status(doc_id: int, status: str, db: Session = Depends(get_db)):
    doc = db.query(DocumentosTomador).filter(DocumentosTomador.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
    
    doc.status = status  # "aceito", "recusado", "pendente"
    db.commit()
    return {"message": "Status atualizado com sucesso", "status": doc.status}
