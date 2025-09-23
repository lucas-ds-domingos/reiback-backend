
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Tomador
from ..schemas.tomador import TomadorBase
import requests

router = APIRouter()
RECEITA_API = "https://www.receitaws.com.br/v1/cnpj/"

def normalizar_cnpj(cnpj: str) -> str:
    return cnpj.replace(".", "").replace("/", "").replace("-", "")


@router.get("/{cnpj}", response_model=TomadorBase)
def get_tomador(cnpj: str, db: Session = Depends(get_db)):
    cnpj = normalizar_cnpj(cnpj)  # <-- normaliza aqui

    tomador = db.query(Tomador).filter(Tomador.cnpj == cnpj).first()
    if tomador:
        return tomador

    response = requests.get(f"{RECEITA_API}{cnpj}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Tomador não encontrado na API")
    data = response.json()

    novo_tomador = Tomador(
        cnpj=cnpj,  # <-- já normalizado
        nome=data.get("nome") or data.get("fantasia"),
        fantasia=data.get("fantasia"),
        endereco=data.get("logradouro"),
        municipio=data.get("municipio"),
        uf=data.get("uf"),
        cep=data.get("cep"),
        capital_social=float(data.get("capital_social", 0)),
        limite_taxa=0.0
    )
    db.add(novo_tomador)
    db.commit()
    db.refresh(novo_tomador)
    return novo_tomador



@router.put("/{cnpj}/atualizar", response_model=TomadorBase)
def atualizar_tomador(cnpj: str, db: Session = Depends(get_db)):
    tomador = db.query(Tomador).filter(Tomador.cnpj == cnpj).first()
    if not tomador:
        raise HTTPException(status_code=404, detail="Tomador não encontrado no banco")

    response = requests.get(f"{RECEITA_API}{cnpj}")
    if response.status_code != 200:
        raise HTTPException(status_code=404, detail="Erro ao buscar API")
    data = response.json()

    tomador.nome = data.get("nome") or data.get("fantasia")
    tomador.fantasia = data.get("fantasia")
    tomador.endereco = data.get("logradouro")
    tomador.municipio = data.get("municipio")
    tomador.uf = data.get("uf")
    tomador.cep = data.get("cep")
    tomador.capital_social = float(data.get("capital_social", 0))
    db.commit()
    db.refresh(tomador)
    return tomador
