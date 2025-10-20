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
    email: str
    senha: str
    cpf: str


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    cpf: Optional[str]
    criado_por: str | None = None  # opcional, usado no master
    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    nome:  str | None = None
    email: str | None = None
    senha: str | None = None
    cpf:   str | None = None