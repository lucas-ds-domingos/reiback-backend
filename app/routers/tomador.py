import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tomador, ClienteAsaas
from ..schemas.tomador import TomadorBase
from ..models import Usuario  
from ..utils.get_current_user import get_current_user  
import os
from dotenv import load_dotenv
from decimal import Decimal
from typing import List

load_dotenv()

router = APIRouter()
RECEITA_API = "https://www.receitaws.com.br/v1/cnpj/"
ASAAS_API = "https://sandbox.asaas.com/api/v3/customers"
ASAAS_KEY = os.getenv("ASAAS_API_KEY")

if not ASAAS_KEY:
    raise RuntimeError("Variável de ambiente ASAAS_API_KEY não encontrada")


def normalizar_cnpj(cnpj: str) -> str:
    """Remove pontos, barras e traços do CNPJ"""
    return cnpj.replace(".", "").replace("/", "").replace("-", "")

def normalizar_telefone(numero: str) -> str:
    """Remove tudo que não for dígito"""
    return "".join(filter(str.isdigit, numero or "")) or "11999999999"


def criar_cliente_asaas(tomador: Tomador, db: Session) -> ClienteAsaas:
    """Cria cliente no Asaas sandbox e salva referência no banco"""
    cliente_existente = db.query(ClienteAsaas).filter(ClienteAsaas.tomador_id == tomador.id).first()
    if cliente_existente:
        return cliente_existente

    payload = {
        "name": tomador.nome or "Cliente Teste",
        "cpfCnpj": normalizar_cnpj(tomador.cnpj),
        "email": tomador.email or "teste@teste.com",
        "phone": normalizar_telefone(tomador.telefone),
        "mobilePhone": normalizar_telefone(tomador.telefone),
        "address": tomador.endereco or "Endereço Teste",
        "province": tomador.municipio or "SP",
        "postalCode": tomador.cep or "01001000",
        "state": tomador.uf or "SP",
        "country": "Brazil"
    }

    headers = {
        "Content-Type": "application/json",
        "access_token": ASAAS_KEY
    }

    response = requests.post(ASAAS_API, headers=headers, json=payload)
    print("Asaas status:", response.status_code)
    print("Asaas response:", response.text)

    if response.status_code not in [200, 201]:
        raise HTTPException(status_code=500, detail=f"Erro ao criar cliente no Asaas: {response.text}")

    res_data = response.json()
    cliente = ClienteAsaas(customer_id=res_data["id"], tomador_id=tomador.id)
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente

# ... (importações e configurações continuam iguais)

@router.get("/{cnpj}", response_model=TomadorBase)
def get_tomador(
    cnpj: str, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user) 
):
    cnpj = normalizar_cnpj(cnpj)

    # 1️⃣ Busca no banco primeiro
    tomador = db.query(Tomador).filter(Tomador.cnpj == cnpj).first()
    if tomador:
        if tomador.usuario_id and tomador.usuario_id != current_user.id:
            raise HTTPException(
                status_code=403, 
                detail="❌ Este tomador já está vinculado a outro usuário."
            )
        if not tomador.asaas_cliente:
            db.commit()  # 🔹 garante que Tomador tenha ID antes de criar cliente Asaas
            criar_cliente_asaas(tomador, db)
        db.refresh(tomador)
        return tomador

    # 2️⃣ Se não existe, busca na Receita
    response = requests.get(f"{RECEITA_API}{cnpj}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Tomador não encontrado na Receita")
    data = response.json()

    # 3️⃣ Cria novo tomador
    novo_tomador = Tomador(
        cnpj=cnpj,
        nome=data.get("nome") or data.get("fantasia") or "Nome Teste",
        fantasia=data.get("fantasia"),
        endereco=f"{data.get('logradouro', '')} {data.get('bairro', '')}".strip() or "Endereço Teste",
        municipio=data.get("municipio") or "SP",
        uf=data.get("uf") or "SP",
        cep=data.get("cep") or "01001000",
        email=data.get("email") or "teste@teste.com",
        telefone=data.get("telefone") or "11999999999",
        capital_social=float(data.get("capital_social", 0)),
        limite_aprovado=Decimal("1000000.00"),
        limite_disponivel=Decimal("1000000.00"),
        usuario_id=current_user.id
    )

    db.add(novo_tomador)
    db.commit()      # 🔹 salva no banco e gera ID
    db.refresh(novo_tomador)

    criar_cliente_asaas(novo_tomador, db)  # 🔹 agora ID já existe
    db.refresh(novo_tomador)
    return novo_tomador


@router.put("/{cnpj}/atualizar", response_model=TomadorBase)
def atualizar_tomador(
    cnpj: str,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cnpj = normalizar_cnpj(cnpj)
    tomador = db.query(Tomador).filter(Tomador.cnpj == cnpj).first()
    if not tomador:
        raise HTTPException(status_code=404, detail="Tomador não encontrado no banco")

    response = requests.get(f"{RECEITA_API}{cnpj}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Erro ao buscar API")
    data = response.json()

    tomador.nome = data.get("nome") or data.get("fantasia") or "Nome Teste"
    tomador.fantasia = data.get("fantasia")
    tomador.endereco = f"{data.get('logradouro', '')} {data.get('bairro', '')}".strip() or "Endereço Teste"
    tomador.municipio = data.get("municipio") or "SP"
    tomador.uf = data.get("uf") or "SP"
    tomador.cep = data.get("cep") or "01001000"
    tomador.email = data.get("email") or "teste@teste.com"
    tomador.telefone = data.get("telefone") or "11999999999"
    tomador.capital_social = float(data.get("capital_social", 0))
    tomador.usuario_id = current_user.id

    db.commit()      # 🔹 salva alterações
    db.refresh(tomador)

    if not tomador.asaas_cliente:
        criar_cliente_asaas(tomador, db)
    db.refresh(tomador)
    return tomador


@router.get("/list-tomador", response_model=List[TomadorBase])
def listar_tomador(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Tomador).filter(Tomador.usuario_id == current_user.id).all()
