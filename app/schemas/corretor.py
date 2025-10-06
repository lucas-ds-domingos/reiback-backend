from pydantic import BaseModel
from typing import Optional
from datetime import date

class CorretoraBase(BaseModel):
    finance_id: int
    cnpj: str
    razao_social: str
    inscricao_municipal: Optional[str] = None
    comissao: Optional[float] = 0.0
    situacao_cnpj: Optional[str] = None
    codigo_cnae: Optional[str] = None
    ramo: Optional[str] = None
    data_registro: Optional[date] = None
    data_recadastro: Optional[date] = None
    data_expiracao: Optional[date] = None
    telefone: Optional[str] = None
    susep: Optional[int] = None
    data_registro: Optional[date] = None

    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    uf: Optional[str] = None
    cidade: Optional[str] = None

class CorretoraCreate(CorretoraBase):
    pass

class CorretoraResponse(CorretoraBase):
    id: int

    model_config = {
    "from_attributes": True
}