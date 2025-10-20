from pydantic import BaseModel, EmailStr
from typing import Optional

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

class LoginSchema(BaseModel):
    email: str
    senha: str


class UsuarioCreateFisico(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    cpf: str
    corretora_id: Optional[int]
    assessoria_id: Optional[int]
    finance_id: Optional[int]