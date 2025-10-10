from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class RepresentanteLegalBase(BaseModel):
    nome_completo: constr(min_length=3, max_length=255)
    cpf: constr(min_length=11, max_length=14)
    email: EmailStr

    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[constr(min_length=2, max_length=2)] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None

class RepresentanteLegalCreate(RepresentanteLegalBase):
    tomador_id: int

class RepresentanteLegalUpdate(BaseModel):
    nome_completo: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None

    endereco: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[constr(min_length=2, max_length=2)] = None
    estado_civil: Optional[str] = None
    profissao: Optional[str] = None

class RepresentanteLegalResponse(RepresentanteLegalBase):
    id: int
    tomador_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = {
        "from_attributes": True
    }