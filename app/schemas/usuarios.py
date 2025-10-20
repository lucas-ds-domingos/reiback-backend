from pydantic import BaseModel, EmailStr

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