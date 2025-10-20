from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class CCGBase(BaseModel):
    tomador_id: int
    fiadores: List[dict]
    representantes_legais: List[dict]

class CCGCreate(CCGBase):
    pass

class CCGResponse(BaseModel):
    id: int
    status: str
    documento_uuid: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True


class CCGList(BaseModel):
    id: int
    status: str
    caminho_pdf: Optional[str] = None
    d4sign_link: Optional[str] = None
    criado_em: datetime

    class Config:
        orm_mode = True