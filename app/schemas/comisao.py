from sqlalchemy import Column, Integer, ForeignKey, DateTime, Numeric, String
from sqlalchemy.orm import relationship
from ..database import Base
from datetime import datetime

class Comissao(Base):
    __tablename__ = "comissoes"

    id = Column(Integer, primary_key=True, index=True)
    apolice_id = Column(Integer, ForeignKey("apolices.id"), nullable=False)
    proposta_id = Column(Integer, ForeignKey("propostas.id"), nullable=False)
    corretor_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    assessoria_id = Column(Integer, ForeignKey("assessorias.id"), nullable=True)

    valor_bruto = Column(Numeric(12, 2), nullable=False)
    valor_corretor = Column(Numeric(12, 2), nullable=False)
    valor_assessoria = Column(Numeric(12, 2), nullable=True)
    status_pagamento = Column(String(50), default="pendente")  
    pago_em = Column(DateTime, nullable=True)
    gerado_em = Column(DateTime, default=datetime.utcnow)

    apolice = relationship("Apolice")
    proposta = relationship("Proposta")
    corretor = relationship("Usuario")
    assessoria = relationship("Assessoria")
