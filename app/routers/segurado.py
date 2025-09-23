from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Segurado
from ..schemas.segurado import SeguradoBase, SeguradoCreate
import requests

router = APIRouter()

@router.get("/{cpf_cnpj}", response_model=SeguradoBase)
def get_segurado(cpf_cnpj: str, db: Session = Depends(get_db)):
    cpf_cnpj_normalizado = "".join(filter(str.isdigit, cpf_cnpj))

    # 1️⃣ Busca no banco
    segurado = db.query(Segurado).filter(Segurado.cpf_cnpj == cpf_cnpj_normalizado).first()
    if segurado:
        return segurado

    # 2️⃣ Se não existe → chama API externa
    url = f"https://receitaws.com.br/v1/cnpj/{cpf_cnpj_normalizado}"
    response = requests.get(url)
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Segurado não encontrado na ReceitaWS")

    dados = response.json()

    # 3️⃣ Cria no banco
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
        email=dados.get("email", None),
        telefone=dados.get("telefone", None),
    )
    db.add(novo_segurado)
    db.commit()
    db.refresh(novo_segurado)

    return novo_segurado
