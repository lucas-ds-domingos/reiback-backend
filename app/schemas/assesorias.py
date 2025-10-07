from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

class AssesoriaBase(BaseModel):
    id: Optional[int]
    cnpj: str
    razao_social: str
    comissao: Optional[float] = 0.0
    data_registro: Optional[date] = None
    data_recadastro: Optional[date] = None
    data_expiracao: Optional[date] = None
    telefone: Optional[str] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    uf: Optional[str] = None
    cidade: Optional[str] = None

class AssesoriaCreate(AssesoriaBase):
    email: str
    password: str
    

class AssesoriaResponse(AssesoriaBase):
    id: int

    model_config = {
        "from_attributes": True
    }
