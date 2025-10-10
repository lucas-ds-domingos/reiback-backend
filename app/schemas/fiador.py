from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class FiadorBase(BaseModel):
    nome_completo: constr(min_length=3, max_length=255)
    cpf_cnpj: constr(min_length=11, max_length=20)
    email: EmailStr
    tipo: constr(min_length=2, max_length=2)  # "PF" ou "PJ"

    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[constr(min_length=2, max_length=2)] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None

class FiadorCreate(FiadorBase):
    tomador_id: int

class FiadorUpdate(BaseModel):
    nome_completo: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    email: Optional[EmailStr] = None
    tipo: Optional[str] = None

    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[constr(min_length=2, max_length=2)] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None

class FiadorResponse(FiadorBase):
    id: int
    tomador_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }