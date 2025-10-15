from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends, APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from ..database import get_db, Base, engine
from ..models import DocumentosTomador
from ..services.google_drive import upload_to_drive

router = APIRouter()

# Cria tabelas
Base.metadata.create_all(bind=engine)


FOLDER_ID = "1vlOKf_aj-o9cHpvSlSG6U7oMM0kg7Lw9"

@app.post("/api/documentos")
async def upload_documentos(
    tomador_id: int = Form(...),
    user_id: int = Form(...),
    contrato_social: UploadFile | None = File(None),
    ultimas_alteracoes: UploadFile | None = File(None),
    balanco: UploadFile | None = File(None),
    ultimas_alteracoes_adicional: UploadFile | None = File(None),
    dre: UploadFile | None = File(None),
    balancete: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    doc = DocumentosTomador(tomador_id=tomador_id, user_id=user_id)

    # Função auxiliar
    async def process(file: UploadFile | None, field_name: str):
        if file:
            # Lê conteúdo
            content = await file.read()
            import io
            bio = io.BytesIO(content)
            # Define nome do arquivo no drive
            filename = f"{tomador_id}_{field_name}_{file.filename}"
            url = upload_to_drive(bio, filename, FOLDER_ID)
            setattr(doc, field_name, url)

    # Processar cada arquivo
    await process(contrato_social, "contrato_social")
    await process(ultimas_alteracoes, "ultimas_alteracoes")
    await process(balanco, "balanco")
    await process(ultimas_alteracoes_adicional, "ultimas_alteracoes_adicional")
    await process(dre, "dre")
    await process(balancete, "balancete")

    # Salvar no banco
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return JSONResponse({"success": True, "documentos": {
        "contrato_social": doc.contrato_social,
        "ultimas_alteracoes": doc.ultimas_alteracoes,
        "balanco": doc.balanco,
        "ultimas_alteracoes_adicional": doc.ultimas_alteracoes_adicional,
        "dre": doc.dre,
        "balancete": doc.balancete,
    }})



@app.get("/api/documentos/{tomador_id}")
def listar_documentos(tomador_id: int, db: Session = Depends(get_db)):
    doc = db.query(DocumentosTomador).filter_by(tomador_id=tomador_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Não encontrado")

    return {
        "tomador_id": doc.tomador_id,
        "user_id": doc.user_id,
        "contrato_social": doc.contrato_social,
        "ultimas_alteracoes": doc.ultimas_alteracoes,
        "balanco": doc.balanco,
        "ultimas_alteracoes_adicional": doc.ultimas_alteracoes_adicional,
        "dre": doc.dre,
        "balancete": doc.balancete,
        "data_upload": doc.data_upload.isoformat(),
    }
