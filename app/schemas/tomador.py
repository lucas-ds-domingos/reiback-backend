from pydantic import BaseModel
from typing import Optional

class TomadorBase(BaseModel):
    id: Optional[int]
    cnpj: str
    nome: str
    fantasia: Optional[str]
    email: Optional[str]
    telefone: Optional[str]
    endereco: Optional[str]
    municipio: Optional[str]
    uf: Optional[str]
    cep: Optional[str]
    capital_social: Optional[float]
    limite_taxa: float

    model_config = {
        "from_attributes": True
    }
