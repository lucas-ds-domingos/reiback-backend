# app/routers/webhook_d4sign.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Apolice
import requests
import os
from dotenv import load_dotenv

load_dotenv()

D4SIGN_BASE_URL = "https://secure.d4sign.com.br/api/v1"
D4SIGN_TOKEN_API = os.getenv("D4SIGN_TOKEN_API")
D4SIGN_CRYPT_KEY = os.getenv("D4SIGN_CRYPT_KEY")

router = APIRouter(
    prefix="/api",
    tags=["Webhook D4Sign"]
)

@router.post("/webhook-d4sign")
def webhook_d4sign(payload: dict, db: Session = Depends(get_db)):
    """
    Webhook que recebe notificações do D4Sign quando um documento é assinado.
    Baixa o PDF assinado e salva no banco.
    """
    # 1️⃣ Verifica se há UUID no payload
    document_id = payload.get("uuid") or payload.get("document_uuid") or payload.get("documentId")
    if not document_id:
        print("⚠️ Payload recebido sem UUID:", payload)
        return {"status": "ignored", "reason": "no uuid in payload"}

    # 2️⃣ Busca a apólice correspondente no banco
    apolice = db.query(Apolice).filter(Apolice.d4sign_document_id == document_id).first()
    if not apolice:
        print(f"⚠️ Apólice não encontrada para UUID {document_id}")
        return {"status": "apolice not found"}

    # 3️⃣ Prepara query params para download
    params = {
        "tokenAPI": D4SIGN_TOKEN_API,
        "cryptKey": D4SIGN_CRYPT_KEY
    }

    # 4️⃣ Faz o download do PDF assinado
    try:
        resp = requests.get(f"{D4SIGN_BASE_URL}/documents/{document_id}/download", params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Erro ao baixar PDF do D4Sign: {e}")
        return {"status": "error", "reason": str(e)}

    if not resp.content:
        print(f"❌ Nenhum conteúdo retornado para documento {document_id}")
        return {"status": "no content"}

    # 5️⃣ Salva PDF assinado no banco
    apolice.pdf_assinado = resp.content
    apolice.status_assinatura = "assinada"
    db.commit()
    db.refresh(apolice)

    print(f"✅ PDF assinado salvo no banco para a apólice {apolice.numero}")
    return {"status": "ok", "document_id": document_id}
