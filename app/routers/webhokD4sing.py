from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CCG
import hmac, hashlib, os

router = APIRouter()

D4SIGN_HMAC_KEY = os.getenv("D4SIGN_CRYPT_KEY_HMAC")

@router.post("/webhook-d4sign")
async def webhook_d4sign(
    request: Request,
    content_hmac: str = Header(None, alias="Content-Hmac"),
    content_hmac_alt: str = Header(None, alias="Content-HMAC"),
    db: Session = Depends(get_db)
):
    # ✅ Aceitar os dois formatos de header
    hmac_received = content_hmac or content_hmac_alt
    if not hmac_received:
        raise HTTPException(status_code=400, detail="HMAC não enviado")

    # ✅ Capturar corpo bruto para verificar o HMAC
    body = await request.body()

    print("HEADERS RECEBIDOS:", request.headers)
    print("BODY RAW RECEBIDO:", body)

    # ✅ Calcular HMAC
    computed_hmac = hmac.new(
        D4SIGN_HMAC_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    print("HMAC RECEBIDO:", hmac_received)
    print("HMAC CALCULADO:", computed_hmac)

    if not hmac.compare_digest(computed_hmac, hmac_received):
        raise HTTPException(status_code=403, detail="HMAC inválido")

    # ✅ Ler o corpo conforme tipo de conteúdo
    if "application/json" in request.headers.get("content-type", ""):
        data = await request.json()
        uuid_doc = data.get("uuid")
        type_post = data.get("type_post")
        message = data.get("message")
    else:
        form = await request.form()
        uuid_doc = form.get("uuid")
        type_post = form.get("type_post")
        message = form.get("message")

    print(f"Webhook recebido: {uuid_doc}, type_post: {type_post}, message: {message}")

    # ✅ Atualizar no banco
    ccg = db.query(CCG).filter(CCG.d4sign_uuid == uuid_doc).first()
    if ccg:
        if type_post == "1":
            ccg.status = "assinado"
        elif type_post == "2":
            ccg.status = "cancelado"
        db.commit()
        print(f"✅ CCG {ccg.id} atualizado para status {ccg.status}")
    else:
        print(f"⚠️ Nenhum registro encontrado com uuid {uuid_doc}")

    return {"ok": True}
