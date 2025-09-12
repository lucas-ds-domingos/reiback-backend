from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, DateTime, Boolean, Text
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime



class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)  # senha criptografada
    ativo = Column(Boolean, default=True)
    role = Column(String(50), default="corretor")  # admin, corretor, segurado
    criado_em = Column(DateTime, default=datetime.utcnow)

    propostas = relationship("Proposta", back_populates="usuario")


class Tomador(Base):
    __tablename__ = "tomadores"

    id = Column(Integer, primary_key=True, index=True)
    cnpj = Column(String(18), unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    fantasia = Column(String(255), nullable=True)
    email = Column(String(120), nullable=True)
    telefone = Column(String(50), nullable=True)
    endereco = Column(String(255), nullable=True)
    municipio = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    cep = Column(String(20), nullable=True)
    capital_social = Column(Float, nullable=True)

    limite_taxa = Column(Float, nullable=False, default=0.0)

    propostas = relationship("Proposta", back_populates="tomador")


class Segurado(Base):
    __tablename__ = "segurados"

    id = Column(Integer, primary_key=True, index=True)
    cpf_cnpj = Column(String(18), unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(120), nullable=True)
    telefone = Column(String(50), nullable=True)
    endereco = Column(String(255), nullable=True)
    municipio = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    cep = Column(String(20), nullable=True)

    propostas = relationship("Proposta", back_populates="segurado")

class Proposta(Base):
    __tablename__ = "propostas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), unique=True, nullable=False)
    data_criacao = Column(Date, default=datetime.utcnow)
    status = Column(String(50), default="rascunho")  # rascunho, aprovada, rejeitada

    # 🔹 Campos adicionais
    grupo = Column(String(100), nullable=True)             # Ex: Automóvel
    modalidade = Column(String(100), nullable=True)        # Ex: RC Facultativo
    subgrupo = Column(String(100), nullable=True)          # Ex: Caminhão
    importancia_segurada = Column(Float, nullable=True)    # Valor segurado
    inicio_vigencia = Column(Date, nullable=True)
    termino_vigencia = Column(Date, nullable=True)
    dias_vigencia = Column(Integer, nullable=True)

    premio = Column(Float, nullable=True)                  # Valor total do seguro pago pelo cliente
    comissao = Column(Float, nullable=True)                # Comissão do corretor/tomador
    coberturas_adicionais = Column(Text, nullable=True)    # JSON/string com lista
    numero_contrato = Column(Integer)

    # 🔹 Relações
    tomador_id = Column(Integer, ForeignKey("tomadores.id"))
    segurado_id = Column(Integer, ForeignKey("segurados.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    tomador = relationship("Tomador", back_populates="propostas")
    segurado = relationship("Segurado", back_populates="propostas")
    apolice = relationship("Apolice", uselist=False, back_populates="proposta")
    usuario = relationship("Usuario", back_populates="propostas")



class Apolice(Base):
    __tablename__ = "apolices"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), unique=True, nullable=False)
    data_criacao = Column(Date, default=datetime.utcnow)
    pdf_path = Column(String(255), nullable=True)

    proposta_id = Column(Integer, ForeignKey("propostas.id"))
    proposta = relationship("Proposta", back_populates="apolice")
