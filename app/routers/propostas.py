from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Proposta
from ..schemas.proposta import PropostaCreate, PropostaResponse
import xml.etree.ElementTree as ET
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
from typing import List

router = APIRouter()

@router.post("/propostas/", response_model=PropostaResponse)
def criar_proposta(payload: PropostaCreate, db: Session = Depends(get_db)):
    usuario_id = payload.usuario_id or 1

    nova = Proposta(
        numero=payload.numero,
        grupo=payload.grupo,
        modalidade=payload.modalidade,
        subgrupo=payload.subgrupo,
        importancia_segurada=payload.importancia_segurada,
        inicio_vigencia=payload.inicio_vigencia,
        termino_vigencia=payload.termino_vigencia,
        dias_vigencia=payload.dias_vigencia,
        premio=Decimal(str(payload.premio)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        comissao_percentual=Decimal(str(payload.comissao_percentual)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        comissao_valor=Decimal(str(payload.comissao_valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        taxa_percentual=Decimal(str(payload.taxa_percentual)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        numero_contrato=payload.numero_contrato,
        edital_processo=payload.edital_processo,
        percentual=payload.percentual,
        tomador_id=payload.tomador_id,
        segurado_id=payload.segurado_id,
        usuario_id=usuario_id,
        text_modelo= payload.text_modelo,
    )

    # Gerar XML automaticamente
    root = ET.Element("Proposta")
    payload_dict = payload.dict(exclude_unset=True, exclude={"xml"})
    for key, value in payload_dict.items():
        ET.SubElement(root, key).text = str(value or "")
    tree = ET.ElementTree(root)
    f = BytesIO()
    tree.write(f, encoding="utf-8", xml_declaration=True)
    nova.xml = f.getvalue().decode()

    db.add(nova)
    db.commit()
    db.refresh(nova)

    return nova


@router.patch("/propostas/{proposta_id}/cancelar", response_model=PropostaResponse)
def cancelar_proposta(proposta_id: int, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Proposta não encontrada")

    if proposta.status == "cancelada":
        return proposta

    if proposta.status == "emitida":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Não é possível cancelar proposta já emitida")

    proposta.status = "cancelada"
    proposta.cancelada_em = datetime.utcnow()
    db.commit()
    db.refresh(proposta)
    return proposta


@router.patch("/propostas/{proposta_id}/emitir", response_model=PropostaResponse)
def emitir_proposta(proposta_id: int, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Proposta não encontrada")

    if proposta.status == "emitida":
        return proposta

    if proposta.status == "cancelada":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Não é possível emitir proposta cancelada")

    # Vai para pre-emissao
    proposta.status = "pre-emissao"
    db.commit() 
    db.refresh(proposta)
    return proposta


@router.get("/", response_model=List[PropostaResponse])
def listar_propostas(db: Session = Depends(get_db)):
    propostas = db.query(Proposta).all()
    return propostas
