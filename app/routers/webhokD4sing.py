from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CCG
import hmac, hashlib, os

router = APIRouter()

# Chave secreta MAC da D4Sign
D4SIGN_HMAC_KEY = os.getenv("D4SIGN_CRYPT_KEY_HMAC")

@router.post("/webhook-d4sign")
async def webhook_d4sign(
    request: Request,
    content_hmac: str = Header(None, alias="Content-Hmac"),
    db: Session = Depends(get_db)
):
    if not content_hmac:
        raise HTTPException(status_code=400, detail="HMAC não enviado")

    # 🔹 Parse do form-data primeiro (UUID necessário para HMAC)
    form = await request.form()
    uuid_doc = form.get("uuid")
    type_post = form.get("type_post")
    message = form.get("message")
    email = form.get("email")

    if not uuid_doc:
        raise HTTPException(status_code=400, detail="UUID do documento não encontrado")

    # 🔹 Calcular HMAC corretamente: SHA256(uuid + secret_key)
    computed_hmac = hmac.new(
        D4SIGN_HMAC_KEY.encode(),
        uuid_doc.encode(),
        hashlib.sha256
    ).hexdigest()

    # 🔹 Remover prefixo sha256= do header recebido
    content_hmac_received = content_hmac.replace("sha256=", "")

    print("HMAC recebido:", content_hmac_received)
    print("HMAC calculado:", computed_hmac)

    # 🔹 Validar HMAC
    if not hmac.compare_digest(computed_hmac, content_hmac_received):
        raise HTTPException(status_code=403, detail="HMAC inválido")

    # 🔹 Atualizar banco
    ccg = db.query(CCG).filter(CCG.d4sign_uuid == uuid_doc).first()
    if ccg:
        if type_post == "1":  # Documento finalizado
            ccg.status = "assinado"
        elif type_post == "2":  # Documento cancelado
            ccg.status = "cancelado"
        elif type_post == "4":  # Assinatura realizada parcialmente
            ccg.status = "parcialmente_assinado"
        db.commit()
        print(f"✅ CCG {ccg.id} atualizado para {ccg.status}")
    else:
        print(f"⚠️ CCG com uuid {uuid_doc} não encontrado")

    print(f"Webhook recebido: uuid={uuid_doc}, type_post={type_post}, message={message}, email={email}")

    return {"ok": True}
