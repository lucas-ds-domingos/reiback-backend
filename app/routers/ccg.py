from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import CCG, Tomador
from ..schemas.ccg import CCGCreate, CCGResponse
from ..services.gerar_ccg_pdf import gerar_pdf_ccg
from ..services.d4sign_service import enviar_para_d4sign

router = APIRouter()

@router.post("/gerar", response_model=CCGResponse)
async def gerar_ccg(data: CCGCreate, db: Session = Depends(get_db)):
    # 1️⃣ Buscar dados completos do tomador
    tomador = db.query(Tomador).filter(Tomador.id == data.tomador_id).first()
    if not tomador:
        raise HTTPException(status_code=404, detail="Tomador não encontrado")

    # 2️⃣ Criar registro da CCG com status "GERANDO"
    ccg = CCG(
        tomador_id=data.tomador_id,
        status="GERANDO",
        caminho_pdf=None  # ainda não gerado
    )
    db.add(ccg)
    db.commit()
    db.refresh(ccg)

    # 3️⃣ Preparar dados completos para o PDF
    pdf_data = {
        "tomador": tomador,
        "fiadores": data.fiadores,
        "representantes_legais": data.representantes_legais,
    }

    # 4️⃣ Gerar PDF com Playwright
    pdf_bytes = await gerar_pdf_ccg(pdf_data)

    # 5️⃣ Salvar PDF no banco (como bytes ou caminho de arquivo)
    ccg.caminho_pdf = pdf_bytes  # se for bytea no Postgres 
    db.commit()
    db.refresh(ccg)

    # 6️⃣ Enviar PDF para D4Sign
    uuid = await enviar_para_d4sign(pdf_bytes, pdf_data, ccg.id, db)

    # 7️⃣ Atualizar status e UUID do documento
    ccg.status = "ENVIADO"
    ccg.documento_uuid = uuid
    db.commit()
    db.refresh(ccg)

    return ccg
