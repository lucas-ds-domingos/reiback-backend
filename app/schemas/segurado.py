from pydantic import BaseModel
from typing import Optional

class SeguradoBase(BaseModel):
    cpf_cnpj: str
    nome: str
    fantasia: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    municipio: Optional[str] = None
    uf: Optional[str] = None
    cep: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

    model_config = {
    "from_attributes": True
}

class SeguradoCreate(SeguradoBase):
    pass
