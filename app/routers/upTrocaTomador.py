from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from supabase import create_client
import os
import time

router = APIRouter()

# Configuração do Supabase
SUPABASE_URL = "https://surlbofnknvgmloladqf.supabase.co"
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

@router.post("/tomador-Troca/upload")
async def upload_arquivo(
    arquivo: UploadFile,
    usuario_id: int = Form(...)
):
    try:
        # Nome do arquivo único
        file_ext = arquivo.filename.split(".")[-1]
        file_name = f"tomador_{usuario_id}_{int(time.time())}.{file_ext}"

        # Lê conteúdo do arquivo
        content = await arquivo.read()

        # Envia para o bucket TrocaDeTomador
        response = supabase.storage.from_("TrocaDeTomador").upload(file_name, content)
        if response.get("error"):
            raise HTTPException(status_code=500, detail=str(response["error"]))

        # Pega URL pública
        public_url = supabase.storage.from_("TrocaDeTomador").get_public_url(file_name)

        return JSONResponse({"message": "Upload realizado", "url": public_url})
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Erro ao enviar arquivo")
