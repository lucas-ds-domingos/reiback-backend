import httpx
from sqlalchemy.orm import Session
from ..models import CCG

D4SIGN_BASE_URL = "https://secure.d4sign.com.br/api/v1"

async def enviar_para_d4sign(pdf_bytes: bytes, data: dict, ccg_id: int, db: Session, workflow: str = "0", message: str = "Por favor, assine o documento"):
    """
    Envia PDF para D4Sign, adiciona signatários e campos, e salva o UUID no banco.
    """
    from os import getenv
    TOKEN_API = getenv("D4SIGN_TOKEN_API")
    CRYPT_KEY = getenv("D4SIGN_CRYPT_KEY")
    UUID_FOLDER = getenv("D4SIGN_SAFE_UUID")

    if not TOKEN_API or not CRYPT_KEY or not UUID_FOLDER:
        raise ValueError("TOKEN_API, CRYPT_KEY ou UUID_FOLDER não configurados")

    headers_json = {"Accept": "application/json", "Content-Type": "application/json"}
    headers_file = {"Accept": "application/json"}

    async with httpx.AsyncClient(timeout=60) as client:
        # 1️⃣ Upload do PDF
        files = {"file": ("CCG.pdf", pdf_bytes, "application/pdf")}
        payload = {"uuid_folder": UUID_FOLDER}
        res = await client.post(
            f"{D4SIGN_BASE_URL}/documents/{UUID_FOLDER}/upload?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}",
            files=files,
            json=payload,
            headers=headers_file
        )
        res.raise_for_status()
        doc_uuid = res.json().get("uuid")
        if not doc_uuid:
            raise ValueError(f"UUID não retornado: {res.text}")
        print(f"✅ Documento enviado para D4Sign. UUID: {doc_uuid}")

        # 2️⃣ Adicionar signatários
        signers = data.get("fiadores", []) + data.get("representantes_legais", [])
        fixed_signers = [
            {"email": "fabio.brambila@reibacksolar.com.br", "act": "4", "foreign": "1"},
            {"email": "carol.zanardelli09@gmail.com", "act": "4", "foreign": "1"},
            {"email": "finance@financeassurance.com.br", "act": "1", "foreign": "1", "certified": "1"},
        ]
        all_signers_payload = [
            {"email": s["email"], "act": "1", "foreign": "1"} if "email" in s else s
            for s in signers
        ] + fixed_signers

        if all_signers_payload:
            res_signers = await client.post(
                f"{D4SIGN_BASE_URL}/documents/{doc_uuid}/createlist?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}",
                json={"signers": all_signers_payload},
                headers=headers_json
            )
            res_signers.raise_for_status()
            print("✍️ Signatários adicionados.")

        # 3️⃣ Adicionar campos de assinatura/rubrica
        fields_payload = []
        for idx, s in enumerate(signers):
            fields_payload.append({
                "page": 1,
                "x": 100 + idx * 50,
                "y": 200,
                "width": 150,
                "height": 30,
                "type": "signature",
                "key_signer": s["email"]
            })
            fields_payload.append({
                "page": 1,
                "x": 100 + idx * 50,
                "y": 180,
                "width": 100,
                "height": 20,
                "type": "initials",
                "key_signer": s["email"]
            })
        if fields_payload:
            res_fields = await client.post(
                f"{D4SIGN_BASE_URL}/documents/{doc_uuid}/addField?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}",
                json={"fields": fields_payload},
                headers=headers_json
            )
            res_fields.raise_for_status()
            print("🖊️ Campos de assinatura adicionados.")

        # 4️⃣ Enviar para assinatura por e-mail
        res_send = await client.post(
            f"{D4SIGN_BASE_URL}/documents/{doc_uuid}/sendtosigner?tokenAPI={TOKEN_API}&cryptKey={CRYPT_KEY}",
            json={"workflow": workflow, "message": message, "skip_email": "0"},
            headers=headers_json
        )
        res_send.raise_for_status()
        print("📤 Documento enviado para assinatura.")

        # 5️⃣ Atualizar banco
        ccg = db.query(CCG).filter(CCG.id == ccg_id).first()
        if ccg:
            ccg.d4sign_uuid = doc_uuid
            ccg.status = "ENVIADO"
            db.commit()
            db.refresh(ccg)

        return doc_uuid
