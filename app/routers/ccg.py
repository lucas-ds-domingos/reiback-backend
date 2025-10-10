from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CCG
from ..schemas.ccg import CCGCreate, CCGResponse
from ..services.gerar_ccg_pdf import gerar_pdf_ccg
from ..services.d4sign_service import enviar_para_d4sign

router = APIRouter()

@router.post("/gerar", response_model=CCGResponse)
async def gerar_ccg(data: CCGCreate, db: Session = Depends(get_db)):
    # 1️⃣ Criar registro inicial
    ccg = CCG(
        tomador_id=data.tomador_id,
        status="GERANDO",
        caminho_pdf="temporario.pdf"  # só para não quebrar o NOT NULL
    )
    db.add(ccg)
    db.commit()
    db.refresh(ccg)

    # 2️⃣ Gerar PDF
    pdf_bytes = await gerar_pdf_ccg(data)

    # 3️⃣ Atualizar registro com PDF real
    # Se você salvar PDF em disco:
    caminho = f"pdfs/ccg_{ccg.id}.pdf"
    with open(caminho, "wb") as f:
        f.write(pdf_bytes)
    
    ccg.caminho_pdf = caminho

    # 4️⃣ Enviar para D4Sign
    uuid = await enviar_para_d4sign(pdf_bytes, data)
    ccg.documento_uuid = uuid
    ccg.status = "ENVIADO"

    db.commit()
    db.refresh(ccg)

    return ccg
