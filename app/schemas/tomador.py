from pydantic import BaseModel
from typing import Optional

class TomadorBase(BaseModel):
    id: Optional[int]
    cnpj: str
    nome: str
    fantasia: Optional[str]
    email: Optional[str]
    telefone: Optional[str]
    endereco: Optional[str]
    municipio: Optional[str]
    uf: Optional[str]
    cep: Optional[str]
    capital_social: Optional[float]
    limite_aprovado: float   # 🔹 novo campo
    limite_disponivel: float # 🔹 novo campo

    model_config = {
        "from_attributes": True
    }
