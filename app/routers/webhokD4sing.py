from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CCG
import hmac, hashlib, os

router = APIRouter()
D4SIGN_HMAC_KEY = os.getenv("D4SIGN_CRYPT_KEY_HMAC")  # sua nova chave HMAC

@router.post("/webhook-d4sign")
async def webhook_d4sign(
    request: Request,
    content_hmac: str = Header(None, alias="Content-Hmac"),
    db: Session = Depends(get_db)
):
    if not content_hmac:
        raise HTTPException(status_code=400, detail="HMAC não enviado")

    # ✅ remover o prefixo 'sha256='
    if content_hmac.startswith("sha256="):
        content_hmac = content_hmac.replace("sha256=", "")

    # ✅ pegar corpo bruto exatamente como chegou
    body = await request.body()

    # ✅ calcular HMAC
    computed_hmac = hmac.new(
        D4SIGN_HMAC_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    print("HMAC recebido:", content_hmac)
    print("HMAC calculado:", computed_hmac)

    if not hmac.compare_digest(computed_hmac, content_hmac):
        raise HTTPException(status_code=403, detail="HMAC inválido")

    # ✅ parse do form-data
    form = await request.form()
    uuid_doc = form.get("uuid")
    type_post = form.get("type_post")
    message = form.get("message")
    email = form.get("email")

    print(f"Webhook recebido: uuid={uuid_doc}, type_post={type_post}, message={message}, email={email}")

    # ✅ atualizar no banco
    ccg = db.query(CCG).filter(CCG.d4sign_uuid == uuid_doc).first()
    if ccg:
        if type_post == "1":
            ccg.status = "assinado"
        elif type_post == "2":
            ccg.status = "cancelado"
        elif type_post == "4":
            ccg.status = "parcialmente_assinado"
        db.commit()
        print(f"✅ CCG {ccg.id} atualizado para {ccg.status}")
    else:
        print(f"⚠️ CCG com uuid {uuid_doc} não encontrado")

    return {"ok": True}
