from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CCG
import hmac, hashlib, os

router = APIRouter()
D4SIGN_HMAC_KEY = os.getenv("D4SIGN_CRYPT_KEY_HMAC")  # mesma chave do .env

@router.post("/webhook-d4sign")
async def webhook_d4sign(
    request: Request, 
    content_hmac: str = Header(None, alias="Content-HMAC"),
    db: Session = Depends(get_db)
):
    # 🔹 Ler corpo bruto
    body = await request.body()

    # 🔹 Validar HMAC
    computed_hmac = hmac.new(
        D4SIGN_HMAC_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(computed_hmac, content_hmac):
        raise HTTPException(status_code=403, detail="HMAC inválido")

    # 🔹 Parse do FORM-DATA
    form = await request.form()
    uuid_doc = form.get("uuid")  # note que no seu exemplo é "uuid", não "uuidDoc"
    type_post = form.get("type_post")
    message = form.get("message")

    print(f"Webhook recebido: {uuid_doc}, type_post: {type_post}, message: {message}")

    # 🔹 Atualizar status no banco
    ccg = db.query(CCG).filter(CCG.d4sign_uuid == uuid_doc).first()
    if ccg:
        if type_post == "1":  # documento finalizado
            ccg.status = "assinado"
            db.commit()
            print(f"✅ CCG {ccg.id} marcado como assinado no banco")
        elif type_post == "2":  # documento cancelado
            ccg.status = "cancelado"
            db.commit()
            print(f"⚠️ CCG {ccg.id} marcado como cancelado no banco")
        # você pode adicionar mais casos para outros tipos (e-mail não entregue, assinatura, etc.)
    else:
        print(f"⚠️ CCG com uuid {uuid_doc} não encontrado no banco")

    return {"ok": True}
