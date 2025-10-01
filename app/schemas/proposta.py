from pydantic import BaseModel, Field, condecimal
from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from .segurado import SeguradoBase
from .tomador import TomadorBase


class PropostaCreate(BaseModel):
    numero: str
    grupo: Optional[str]
    modalidade: Optional[str] = None
    subgrupo: Optional[str]
    importancia_segurada: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    inicio_vigencia: Optional[date]
    termino_vigencia: Optional[date]
    dias_vigencia: Optional[int]

    # Financeiro
    premio: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    comissao_percentual: Optional[condecimal(max_digits=5, decimal_places=2)] = Field(default=Decimal("20.00"))
    comissao_valor: Optional[condecimal(max_digits=12, decimal_places=2)] = None
    taxa_percentual: Optional[condecimal(max_digits=5, decimal_places=2)]
    percentual: Optional[condecimal(max_digits=5, decimal_places=2)] = None

    # Dados da etapa de risco
    numero_contrato: Optional[str]
    edital_processo: Optional[str] = None
    text_modelo: Optional[str] = None
    xml: Optional[str] = None

    # Relações
    tomador_id: Optional[int]
    segurado_id: Optional[int]
    usuario_id: Optional[int]

    model_config = {
        "from_attributes": True  
    }


class PropostaResponse(BaseModel):
    id: int
    numero: str
    numero_contrato: Optional[str]
    inicio_vigencia: date
    termino_vigencia: date
    premio: Decimal
    tomador: Optional[TomadorBase]
    segurado: Optional[SeguradoBase]
    status: Optional[str]
    importancia_segurada: Optional[condecimal(max_digits=12, decimal_places=2)] = None

    # 🔹 novos campos
    link_pagamento: Optional[str] = None
    pago_em: Optional[datetime] = None
    valor_pago: Optional[condecimal(max_digits=12, decimal_places=2)] = None

    model_config = {
        "from_attributes": True 
    }
