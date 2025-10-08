from pydantic import BaseModel, EmailStr, constr
from typing import Optional
from datetime import datetime

class RepresentanteLegalBase(BaseModel):
    nome_completo: constr(min_length=3, max_length=255)
    cpf: constr(min_length=11, max_length=14)
    email: EmailStr

class RepresentanteLegalCreate(RepresentanteLegalBase):
    tomador_id: int

class RepresentanteLegalUpdate(BaseModel):
    nome_completo: Optional[str] = None
    cpf: Optional[str] = None
    email: Optional[EmailStr] = None

class RepresentanteLegalResponse(RepresentanteLegalBase):
    id: int
    tomador_id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    model_config = {
    "from_attributes": True
}

