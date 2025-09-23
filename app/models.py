from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, DateTime, Boolean, Text, Numeric
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from decimal import Decimal



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
    fantasia = Column(String(255), nullable=True)

    logradouro = Column(String(255), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(255), nullable=True)
    bairro = Column(String(100), nullable=True)
    municipio = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    cep = Column(String(20), nullable=True)

    email = Column(String(120), nullable=True)
    telefone = Column(String(50), nullable=True)

    # Relacionamento com propostas (se existir)
    propostas = relationship("Proposta", back_populates="segurado")

class Proposta(Base):
    __tablename__ = "propostas"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), unique=True, nullable=False)
    data_criacao = Column(DateTime, default=datetime.utcnow)
    status = Column(String(50), default="rascunho")  # rascunho, aprovada, rejeitada

    # Dados gerais
    grupo = Column(String(100), nullable=True)
    modalidade = Column(String(100), nullable=True)
    subgrupo = Column(String(100), nullable=True)
    importancia_segurada = Column(Numeric(12, 2), nullable=True)
    inicio_vigencia = Column(Date, nullable=True)
    termino_vigencia = Column(Date, nullable=True)
    dias_vigencia = Column(Integer, nullable=True)
    emitida_em = Column(DateTime, nullable=True)
    cancelada_em = Column(DateTime, nullable=True)

    # Financeiro
    taxa_percentual = Column(Numeric(5, 2), nullable=False, default=Decimal("5.00"))
    comissao_percentual = Column(Numeric(5, 2), nullable=False, default=Decimal("20.00"))
    premio = Column(Numeric(12, 2), nullable=True)
    comissao_valor = Column(Numeric(12, 2), nullable=True)

    # Dados da etapa de risco
    numero_contrato = Column(String(50), nullable=True)
    edital_processo = Column(String(100), nullable=True)
    percentual = Column(Numeric(5, 2), nullable=True)
    text_modelo = Column(String(250), nullable=True)

    xml = Column(Text, nullable=True)

    # Relações
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
