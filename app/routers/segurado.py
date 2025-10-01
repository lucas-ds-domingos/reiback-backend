from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Segurado
from ..schemas.segurado import SeguradoBase
import requests

router = APIRouter()

@router.get("/{cpf_cnpj}", response_model=SeguradoBase)
def get_segurado(cpf_cnpj: str, db: Session = Depends(get_db)):
    # Normaliza CPF/CNPJ
    cpf_cnpj_normalizado = "".join(filter(str.isdigit, cpf_cnpj))

    # 1️⃣ Busca no banco
    segurado = db.query(Segurado).filter(Segurado.cpf_cnpj == cpf_cnpj_normalizado).first()
    if segurado:
        return segurado

    # 2️⃣ Se não existe → chama API externa (ReceitaWS)
    url = f"https://receitaws.com.br/v1/cnpj/{cpf_cnpj_normalizado}"
    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException:
        raise HTTPException(status_code=503, detail="Erro ao consultar a ReceitaWS")

    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Segurado não encontrado na ReceitaWS")

    dados = response.json()
    if dados.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=dados.get("message", "Segurado não encontrado"))

    # 3️⃣ Cria novo segurado no banco
    novo_segurado = Segurado(
        cpf_cnpj=cpf_cnpj_normalizado,
        nome=dados.get("nome", ""),
        fantasia=dados.get("fantasia", ""),
        logradouro=dados.get("logradouro", ""),
        numero=dados.get("numero", ""),
        complemento=dados.get("complemento", ""),
        bairro=dados.get("bairro", ""),
        municipio=dados.get("municipio", ""),
        uf=dados.get("uf", ""),
        cep=dados.get("cep", ""),
        email=dados.get("email"),
        telefone=dados.get("telefone"),
    )

    db.add(novo_segurado)
    db.commit()
    db.refresh(novo_segurado)

    return novo_segurado
