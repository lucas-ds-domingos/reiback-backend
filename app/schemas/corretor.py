from pydantic import BaseModel, validator
from typing import Optional
from datetime import date

class CorretoraBase(BaseModel):
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
    assessoria_id: Optional[int] = None
    cep: Optional[str] = None
    endereco: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    uf: Optional[str] = None
    cidade: Optional[str] = None
    pix: Optional[str]

class CorretoraCreate(CorretoraBase):
    email: str
    password: str
    
    @validator("susep", pre=True)
    def str_to_int(cls, v):
        if v is None or v == "":
            return None
        return int(v)
    
class CorretoraUpdate(BaseModel):
    razao_social: Optional[str]
    telefone: Optional[str]
    endereco: Optional[str]
    numero: Optional[str]
    complemento: Optional[str]
    bairro: Optional[str]
    cidade: Optional[str]
    uf: Optional[str]
    cep: Optional[str]
    susep: Optional[int]

class CorretoraUpdateFinanceiro(BaseModel):
    banco: Optional[str]
    bancoOutro: Optional[str] = None 
    tipo_conta: Optional[str]
    agencia: Optional[str]
    digito_agencia: Optional[str]
    conta: Optional[str]
    digito_conta: Optional[str]
    pix: Optional[str]

class CorretoraResponse(CorretoraBase):
    id: int

    model_config = {
        "from_attributes": True
    }


from pydantic import BaseModel

class ResponsavelUpdate(BaseModel):
    nome: str | None = None
    email: str | None = None
    telefone: str | None = None
    cpf: str | None = None
    corretora_id: int
