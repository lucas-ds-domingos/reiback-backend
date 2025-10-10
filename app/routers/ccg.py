from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CCG
from ..schemas.ccg import CCGCreate, CCGResponse
from ..services.gerar_ccg_pdf import gerar_ccg_pdf
from ..services.d4sign_service import enviar_para_d4sign

router = APIRouter(prefix="/ccg", tags=["CCG"])

@router.post("/gerar", response_model=CCGResponse)
async def gerar_ccg(data: CCGCreate, db: Session = Depends(get_db)):
    # Cria registro
    ccg = CCG(tomador_id=data.tomador_id, status="GERANDO")
    db.add(ccg)
    db.commit()
    db.refresh(ccg)

    # Gera PDF
    pdf_bytes = await gerar_ccg_pdf(data)

    # Envia para D4Sign
    uuid = await enviar_para_d4sign(pdf_bytes, data)

    ccg.status = "ENVIADO"
    ccg.documento_uuid = uuid
    db.commit()
    db.refresh(ccg)

    return ccg
