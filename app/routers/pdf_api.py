from fastapi import APIRouter, Request, Response, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta
from ..services.pdf_service import montar_html_apolice, gerar_pdf_playwright, PropostaPayload

router = APIRouter()

@router.post("/", response_class=Response)
async def gerar_pdf(payload: PropostaPayload, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == payload.propostaId).first()
    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    html_content = montar_html_apolice(proposta, payload.textoCompleto)
    pdf_bytes = await run_in_threadpool(gerar_pdf_playwright, html_content)

    return Response(content=pdf_bytes, media_type="application/pdf")
