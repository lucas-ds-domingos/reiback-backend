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
