from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, aliased
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
from sqlalchemy import or_

router = APIRouter()

@router.post("/propostas/", response_model=PropostaResponse)
def criar_proposta(payload: PropostaCreate, db: Session = Depends(get_db)):
    usuario_id = payload.usuario_id  # vem do front
    usuario_adicional_id = None       # padrão

    # ======== Verificação de CCG assinado ========
    usuario_logado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario_logado:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # só checa CCG se não for master
    if usuario_logado.role.lower() != "master":
        ccg_assinado = (
            db.query(CCG)
            .filter(CCG.tomador_id == payload.tomador_id)
            .filter(CCG.status == "assinado")
            .first()
        )
        if not ccg_assinado:
            raise HTTPException(
                status_code=400,
                detail="CCG não assinada. É necessário assinar a CCG antes de criar a proposta."
            )

    # ======== Verifica se é usuário adicional ========
    usuario_logado = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if usuario_logado and usuario_logado.role.lower() == "corretor-adicional":
        usuario_adicional_id = payload.usuario_id  # mantém o adicional

        # busca o usuário principal vinculado à corretora / assessoria / financeira
        usuario_principal = None

        if usuario_logado.corretora_id:
            usuario_principal = db.query(Usuario).filter(
                Usuario.corretora_id == usuario_logado.corretora_id,
                Usuario.role == "corretor"
            ).first()

        elif usuario_logado.assessoria_id:
            usuario_principal = db.query(Usuario).filter(
                Usuario.assessoria_id == usuario_logado.assessoria_id,
                Usuario.role == "assessoria"
            ).first()

        elif usuario_logado.finance_id:
            usuario_principal = db.query(Usuario).filter(
                Usuario.finance_id == usuario_logado.finance_id,
                Usuario.role == "finance"
            ).first()

        # se achou o principal, substitui o usuario_id
        if usuario_principal:
            usuario_id = usuario_principal.id

    # ======== Verificação de limite ========
    tomador = db.query(Tomador).filter(Tomador.id == payload.tomador_id).first()
    if not tomador:
        raise HTTPException(status_code=404, detail="Tomador não encontrado.")

    limite_disponivel = tomador.limite_disponivel or 0
    if limite_disponivel <= 0:
        raise HTTPException(
            status_code=403,
            detail=f"Tomador sem limite disponível. Limite atual: {limite_disponivel}."
        )
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
        usuario_id=usuario_id,                   # vínculo REAL (usuário principal)
        usuario_adicional_id=usuario_adicional_id,  # usuário adicional
        text_modelo=payload.text_modelo,
        tipo_emp=payload.tipo_emp,
        emitida_em=datetime.now(),
    )

    # desconta o limite
    tomador.limite_disponivel -= payload.importancia_segurada
    db.add(tomador)

    # ======== Gerar XML ========
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
def listar_propostas(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    usuario = current_user

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Master vê tudo
    if usuario.role == "master":
        propostas = db.query(Proposta).all()

    # Assessoria vê propostas dos usuários da mesma assessoria
    elif usuario.role == "assessoria":
        propostas = (
            db.query(Proposta)
            .join(Usuario, Proposta.usuario_id == Usuario.id)
            .filter(Usuario.assessoria_id == usuario.assessoria_id)
            .all()
        )

    # Usuário adicional
    elif usuario.role and usuario.role.lower().endswith("-adicional"):
        propostas = (
            db.query(Proposta)
            .filter(Proposta.usuario_adicional_id == usuario.id)
            .all()
        )

    # Usuários normais (corretor, finance, etc.)
    else:
        propostas = db.query(Proposta).filter(Proposta.usuario_id == usuario.id).all()

    # Montar resposta com nomes e objetos tomador/segurado
    result = []
    for p in propostas:
        item = p.__dict__.copy()

        # Nomes do usuário principal e adicional
        item["usuario_principal_nome"] = p.usuario.nome if p.usuario else None
        item["usuario_adicional_nome"] = p.usuario_adicional.nome if p.usuario_adicional else None

        # Objeto tomador
        item["tomador"] = {
            "id": p.tomador.id if p.tomador else None,
            "nome": p.tomador.nome if p.tomador else None,
            "email": p.tomador.email if p.tomador else None,
        }

        # Objeto segurado
        item["segurado"] = {
            "id": p.segurado.id if p.segurado else None,
            "nome": p.segurado.nome if p.segurado else None,
            "email": p.segurado.email if p.segurado else None,
        }

        result.append(item)

    return result

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

    
@router.get("/propostas-Resumo/{proposta_id}", response_model=PropostaResponse)
def obter_proposta(proposta_id: int, db: Session = Depends(get_db)):
    proposta = (
        db.query(Proposta)
        .options(
            joinedload(Proposta.tomador),   
            joinedload(Proposta.segurado),  
            joinedload(Proposta.usuario),    
        )
        .filter(Proposta.id == proposta_id)
        .first()
    )

    if not proposta:
        raise HTTPException(status_code=404, detail="Proposta não encontrada")

    return proposta