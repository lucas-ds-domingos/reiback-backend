from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.proposta import PropostaCreate, PropostaResponse
import xml.etree.ElementTree as ET
from io import BytesIO
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
from typing import List
import os
import requests
from ..models import Proposta, ClienteAsaas, Tomador, Usuario, CCG
from ..utils.get_current_user import get_current_user

router = APIRouter()

@router.post("/propostas/", response_model=PropostaResponse)
def criar_proposta(payload: PropostaCreate, db: Session = Depends(get_db)):
    usuario_id = payload.usuario_id or 1
       
        # ======== Verificação de CCG assinado ========
    ccg_assinado = (
        db.query(CCG)
        .filter(CCG.tomador_id == payload.tomador_id)
        .filter(CCG.status == "assinado") 
        .first()
    )
    if not ccg_assinado:
        raise HTTPException(status_code=400, detail="CCG não assinada. É necessário assinar a CCG antes de criar a proposta.")
    


    # ======== Verificação de limite disponível ========
    tomador = db.query(Tomador).filter(Tomador.id == payload.tomador_id).first()

    if not tomador:
        raise HTTPException(status_code=404, detail="Tomador não encontrado.")

    limite_disponivel = tomador.limite_disponivel or 0

    # Bloqueia se limite <= 0
    if limite_disponivel <= 0:
        raise HTTPException(
            status_code=403,
            detail=f"Tomador sem limite disponível. Limite atual: {limite_disponivel}."
        )

    # Bloqueia se proposta for maior que o limite disponível
    if payload.importancia_segurada > limite_disponivel:
        raise HTTPException(
            status_code=422,
            detail=f"Limite insuficiente. Limite atual: {limite_disponivel}, valor da proposta: {payload.importancia_segurada}."
        )

    # ======== Criação da proposta ========
    nova = Proposta(
        numero=payload.numero,
        grupo=payload.grupo,
        modalidade=payload.modalidade,
        subgrupo=payload.subgrupo,
        importancia_segurada=payload.importancia_segurada,
        inicio_vigencia=payload.inicio_vigencia,
        termino_vigencia=payload.termino_vigencia,
        dias_vigencia=payload.dias_vigencia,
        premio=Decimal(str(payload.premio)).quantize(Decimal("0.01")),
        comissao_percentual=Decimal(str(payload.comissao_percentual)).quantize(Decimal("0.01")),
        comissao_valor=Decimal(str(payload.comissao_valor)).quantize(Decimal("0.01")),
        taxa_percentual=Decimal(str(payload.taxa_percentual)).quantize(Decimal("0.01")),
        numero_contrato=payload.numero_contrato,
        edital_processo=payload.edital_processo,
        percentual=payload.percentual,
        tomador_id=payload.tomador_id,
        segurado_id=payload.segurado_id,
        usuario_id=usuario_id,
        text_modelo=payload.text_modelo,
        tipo_emp=payload.tipo_emp,
        emitida_em=datetime.now(),
    )

    # Desconta o limite
    tomador.limite_disponivel = limite_disponivel - payload.importancia_segurada
    db.add(tomador)

    # Gerar XML automaticamente
    import xml.etree.ElementTree as ET
    from io import BytesIO
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
    db.refresh(tomador)

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


ASAAS_API_KEY = os.getenv("ASAAS_API_KEY")
ASAAS_BASE_URL = "https://sandbox.asaas.com/api/v3" 
@router.patch("/propostas/{proposta_id}/emitir")
def emitir_proposta(proposta_id: int, db: Session = Depends(get_db)):
    # Busca a proposta
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(404, "Proposta não encontrada")

    # Se já estiver emitida, retorna o link existente
    if proposta.status in ["emitida - pendente pagamento", "paga"]:
        return {
            "proposta_id": proposta.id,
            "status": proposta.status,
            "link_pagamento": proposta.link_pagamento
        }

    # Busca cliente Asaas vinculado ao tomador
    cliente_asaas = db.query(ClienteAsaas).filter(ClienteAsaas.tomador_id == proposta.tomador_id).first()
    if not cliente_asaas:
        raise HTTPException(400, "Cliente Asaas não encontrado para este tomador")

    # Atualiza status para pré-emissão
    proposta.status = "pre-emissao"
    db.commit()
    db.refresh(proposta)

    # Só gera link se não existir
    if not proposta.link_pagamento:
        data = {
            "customer": cliente_asaas.customer_id,
            "billingType": "PIX",
            "dueDate": (datetime.utcnow().date() + timedelta(days=5)).isoformat(),  # vencimento 5 dias
            "value": float(proposta.premio),
            "description": f"Pagamento da proposta {proposta.numero}",
            "externalReference": str(proposta.id)
        }
        headers = {
            "access_token": ASAAS_API_KEY,
            "Content-Type": "application/json"
        }

        response = requests.post(f"{ASAAS_BASE_URL}/payments", json=data, headers=headers)

        if response.status_code not in (200, 201):
            try:
                detail = response.json()
            except ValueError:
                detail = response.text
            raise HTTPException(status_code=400, detail=detail)

        pagamento = response.json()
        proposta.link_pagamento = pagamento.get("invoiceUrl")

    # Atualiza status para emitida - pendente pagamento
    proposta.status = "emitida - pendente pagamento"
    db.commit()
    db.refresh(proposta)

    return {
        "proposta_id": proposta.id,
        "status": proposta.status,
        "link_pagamento": proposta.link_pagamento
    }

@router.get("/propostas-buscar", response_model=List[PropostaResponse])
def listar_propostas(
    db: Session = Depends(get_db),
    current_user_data: Usuario = Depends(get_current_user)  # tipado como Usuario
):
    # Se já é um objeto Usuario, não precisa buscar no banco de novo
    usuario = current_user_data

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if usuario.role == "master":
        propostas = db.query(Proposta).all()

    elif usuario.role == "assessoria":
        propostas = (
            db.query(Proposta)
            .join(Usuario, Proposta.usuario_id == Usuario.id)
            .filter(Usuario.assessoria_id == usuario.assessoria_id)
            .all()
        )

    else:
        propostas = db.query(Proposta).filter(Proposta.usuario_id == usuario.id).all()

    return propostas


@router.get("/propostas/{proposta_id}", response_model=PropostaResponse)
def obter_proposta(proposta_id: int, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(404, "Proposta não encontrada")
    return proposta



@router.get("/propostas/{proposta_id}/link-pagamento")
def obter_link_pagamento(proposta_id: int, db: Session = Depends(get_db)):
    proposta = db.query(Proposta).filter(Proposta.id == proposta_id).first()
    if not proposta:
        raise HTTPException(404, "Proposta não encontrada")
    
    # Buscar cliente Asaas
    cliente_asaas = db.query(ClienteAsaas).filter(ClienteAsaas.tomador_id == proposta.tomador_id).first()
    if not cliente_asaas:
        raise HTTPException(400, "Cliente Asaas não encontrado")

    data = {
        "customer": cliente_asaas.customer_id,
        "billingType": "PIX",
        "dueDate": datetime.utcnow().date().isoformat(),
        "value": float(proposta.premio),
        "description": f"Pagamento da proposta {proposta.id}",
        "externalReference": str(proposta.id)
    }
    headers = {"access_token": ASAAS_API_KEY, "Content-Type": "application/json"}
    response = requests.post(f"{ASAAS_BASE_URL}/payments", json=data, headers=headers)
    if response.status_code not in (200, 201):
        raise HTTPException(400, "Erro ao gerar link de pagamento")

    pagamento = response.json()
    return {"link_pagamento": pagamento.get("invoiceUrl")}

    
