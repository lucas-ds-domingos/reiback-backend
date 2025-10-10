from fastapi import APIRouter, Request, Header, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CCG
import hmac, hashlib, json
import os

router = APIRouter()
D4SIGN_HMAC_KEY = os.getenv("D4SIGN_CRYPT_KEY_HMAC")  # mesma chave que você colocou no .env

@router.post("/webhook-d4sign")
async def webhook_d4sign(request: Request, content_hmac: str = Header(None)):
    body = await request.body()

    # 🔹 Validação do HMAC
    computed_hmac = hmac.new(
        D4SIGN_HMAC_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hmac, content_hmac):
        raise HTTPException(status_code=403, detail="HMAC inválido")

    form = await request.form()
    uuid_doc = form.get("uuidDoc")
    status = form.get("status")
    signers = form.get("signers")

    print(f"Documento {uuid_doc} mudou para {status}. Signers: {signers}")

    # 🔹 Atualiza status no banco
    db: Session = next(get_db())
    ccg = db.query(CCG).filter(CCG.d4sign_uuid == uuid_doc).first()
    if ccg:
        if status.lower() == "assinado":
            ccg.status = "assinado"
            db.commit()
            print(f"✅ CCG {ccg.id} marcado como assinado no banco")
    else:
        print(f"⚠️ CCG com uuid {uuid_doc} não encontrado no banco")

    return {"ok": True}
