from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CCG
import hmac, hashlib, json
from os import getenv
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

D4SIGN_HMAC_KEY = getenv("D4SIGN_CRYPT_KEY_HMAC")
if not D4SIGN_HMAC_KEY:
    raise RuntimeError("Variável D4SIGN_CRYPT_KEY_HMAC não encontrada no ambiente")

@router.post("/webhook-d4sign")
async def webhook_d4sign(
    request: Request,
    content_hmac: str = Header(None),
    db: Session = Depends(get_db)
):
    body = await request.body()

    # 🔹 Validação do HMAC
    computed_hmac = hmac.new(D4SIGN_HMAC_KEY.encode(), body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed_hmac, content_hmac):
        raise HTTPException(status_code=403, detail="HMAC inválido")

    form = await request.form()
    uuid_doc = form.get("uuidDoc")
    status = form.get("status")
    signers = form.get("signers")

    print(f"Documento {uuid_doc} mudou para {status}. Signers: {signers}")

    # 🔹 Atualiza status no banco
    ccg = db.query(CCG).filter(CCG.d4sign_uuid == uuid_doc).first()
    if ccg:
        if status.lower() in ["assinado", "signed", "concluido"]:  # ajuste conforme retorno real
            ccg.status = "assinado"
            db.commit()
            print(f"✅ CCG {ccg.id} marcado como assinado no banco")
    else:
        print(f"⚠️ CCG com uuid {uuid_doc} não encontrado no banco")

    return {"ok": True}
