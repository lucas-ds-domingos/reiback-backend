from pydantic import BaseModel
from datetime import datetime

class ClienteAsaasBase(BaseModel):
    tomador_id: int
    asaas_id: str

class ClienteAsaasResponse(ClienteAsaasBase):
    id: int
    data_criacao: datetime

model_config = {
    "from_attributes": True
}