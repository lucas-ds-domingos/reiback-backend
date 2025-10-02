import time
import requests
from io import BytesIO
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Apolice
from ..services.pdf_service import montar_html_apolice, gerar_pdf_playwright
from dotenv import load_dotenv
import os
import json
import asyncio

load_dotenv()

# ---------------------- CONFIGURAÇÃO ----------------------
D4SIGN_BASE_URL = "https://secure.d4sign.com.br/api/v1"
D4SIGN_TOKEN_API = os.getenv("D4SIGN_TOKEN_API")
D4SIGN_CRYPT_KEY = os.getenv("D4SIGN_CRYPT_KEY")
D4SIGN_SAFE_UUID = os.getenv("D4SIGN_SAFE_UUID")  # UUID do cofre/live
D4SIGN_FOLDER_UUID = os.getenv("D4SIGN_FOLDER_UUID")
D4SIGN_EMAIL = os.getenv("D4SIGN_EMAIL")  # <-- email do dono da conta
# -----------------------------------------------------------

def enviar_para_d4sign_e_salvar(apolice_id: int, timeout=300, interval=5):
    db: Session = SessionLocal()
    try:
        # ---------------------- BUSCA APÓLICE ----------------------
        ap = db.query(Apolice).filter(Apolice.id == apolice_id).first()
        if not ap:
            print(f"❌ Apólice {apolice_id} não encontrada")
            return
        proposta = ap.proposta
        if not proposta:
            print(f"❌ Proposta da apólice {apolice_id} não encontrada")
            return

        # ---------------------- GERAR PDF ----------------------
        html = montar_html_apolice(proposta)
        pdf_bytes = asyncio.run(gerar_pdf_playwright(html))
        print(f"✅ PDF gerado para apólice {ap.numero} ({len(pdf_bytes)} bytes)")
        

        if not D4SIGN_TOKEN_API or not D4SIGN_CRYPT_KEY or not D4SIGN_SAFE_UUID:
            print("❌ TokenAPI, CryptKey ou uuid_safe não configurados")
            return

        # ---------------------- CRIAR DOCUMENTO (UPLOAD) ----------------------
        files = {"file": ("apolice.pdf", BytesIO(pdf_bytes), "application/pdf")}
        data = {"uuid_folder": D4SIGN_FOLDER_UUID, "name": f"Apolice-{ap.numero}"}

        create_url = f"{D4SIGN_BASE_URL}/documents/{D4SIGN_SAFE_UUID}/upload?tokenAPI={D4SIGN_TOKEN_API}&cryptKey={D4SIGN_CRYPT_KEY}"
        resp_create = requests.post(create_url, files=files, data=data)

        print("📡 Status criação:", resp_create.status_code)
        print("📡 Resposta criação completa:")
        print(resp_create.text[:1000])

        document_uuid = None
        try:
            document_uuid = resp_create.json().get("uuid")
        except json.JSONDecodeError:
            print("⚠️ Resposta não é JSON, não foi possível obter UUID.")

        if not document_uuid:
            print("❌ Documento não criado ou UUID não retornado. Verifique o painel D4Sign.")
            return
        print(f"✅ Documento criado com UUID: {document_uuid}")

        # ---------------------- CRIAR SIGNATÁRIO ----------------------
        signer_url = f"{D4SIGN_BASE_URL}/documents/{document_uuid}/createlist?tokenAPI={D4SIGN_TOKEN_API}&cryptKey={D4SIGN_CRYPT_KEY}"
        payload_signer = {
            "signers": [
                {
                    "email": D4SIGN_EMAIL,
                    "act": "1", 
                    "foreign": "0"
                }
            ]
        }
        resp_signer = requests.post(signer_url, json=payload_signer)
        print("📡 Status criar signatário:", resp_signer.status_code)
        print("📡 Resposta criar signatário:", resp_signer.text[:500])
        resp_signer.raise_for_status()
        print("✅ Signatário criado")

        # ---------------------- DEFINIR POSIÇÃO DA ASSINATURA ----------------------
        pos_url = f"{D4SIGN_BASE_URL}/documents/{document_uuid}/signatures?tokenAPI={D4SIGN_TOKEN_API}&cryptKey={D4SIGN_CRYPT_KEY}"
        payload_pos = {
            "signatures": [
                    {
                    "email": D4SIGN_EMAIL,
                    "act": "1",
                    "certificadoicpbr": "1",
                    "posx": "150",       
                    "posy": "500",     
                    "page": "2",        
                    "reason": "Assinatura da Apólice"
                    }
            ]
        }
        resp_pos = requests.post(pos_url, json=payload_pos)
        print("📡 Status posição assinatura:", resp_pos.status_code)
        print("📡 Resposta posição assinatura:", resp_pos.text[:500])
        resp_pos.raise_for_status()
        print("✅ Posição da assinatura definida")

        # ---------------------- ASSINATURA AUTOMÁTICA COM A1 ----------------------
        sign_url = f"{D4SIGN_BASE_URL}/documents/{document_uuid}/sign?tokenAPI={D4SIGN_TOKEN_API}&cryptKey={D4SIGN_CRYPT_KEY}"
        payload_sign = {"certificadoicpbr": "1"}
        resp_sign = requests.post(sign_url, json=payload_sign)

        print("📡 Status assinatura automática:", resp_sign.status_code)
        print("📡 Resposta assinatura automática:")
        print(resp_sign.text[:1000])
        resp_sign.raise_for_status()
        print(f"✅ Documento assinado automaticamente: {document_uuid}")

        # ---------------------- BAIXAR PDF ASSINADO ----------------------
        download_url = f"{D4SIGN_BASE_URL}/documents/{document_uuid}/download?tokenAPI={D4SIGN_TOKEN_API}&cryptKey={D4SIGN_CRYPT_KEY}"
        payload_download = {"type": "pdf", "document": "true"}
        resp_dl = requests.post(download_url, json=payload_download)

        print("📡 Status download:", resp_dl.status_code)
        print("📡 Resposta download:")
        print(resp_dl.text[:1000])
        resp_dl.raise_for_status()

        download_link = None
        try:
            download_link = resp_dl.json().get("url")
        except json.JSONDecodeError:
            print("⚠️ Download response não é JSON.")

        if not download_link:
            print("❌ URL de download não retornada")
            return

        pdf_assinado_bytes = requests.get(download_link).content
        print(f"✅ PDF assinado baixado ({len(pdf_assinado_bytes)} bytes)")

        # ---------------------- SALVAR NO BANCO ----------------------
        ap.pdf_assinado = pdf_assinado_bytes
        ap.d4sign_document_id = document_uuid
        ap.status_assinatura = "assinada"
        db.commit()
        db.refresh(ap)
        print(f"🎉 PDF assinado salvo na apólice {ap.numero}")

    except Exception as e:
        print("❌ Erro no fluxo D4Sign:", e)
    finally:
        db.close()
