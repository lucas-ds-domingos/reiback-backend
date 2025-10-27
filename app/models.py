from sqlalchemy import Column, Integer, String, ForeignKey, Date, Float, DateTime, Boolean, Text, Numeric, LargeBinary, JSON, TIMESTAMP,CheckConstraint
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
from decimal import Decimal
from sqlalchemy.sql import func


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    ativo = Column(Boolean, default=True)
    role = Column(String(50), default="corretor")  # master, corretor, corretora
    criado_em = Column(DateTime, default=datetime.utcnow)

    cpf = Column(String(14), unique=True, nullable=True)

    finance_id = Column(Integer, ForeignKey("finances.id"), nullable=True)
    corretora_id = Column(Integer, ForeignKey("corretoras.id"), nullable=True)
    assessoria_id = Column(Integer, ForeignKey("assessorias.id"), nullable=True)

    finance = relationship("Finance", back_populates="usuarios")
    corretora = relationship("Corretora", back_populates="usuarios")
    assessoria = relationship("Assessoria", back_populates="usuarios")

    propostas = relationship("Proposta", back_populates="usuario")
    tomadores = relationship("Tomador", back_populates="usuario")
    password_resets = relationship("PasswordReset", back_populates="usuario")





class PasswordReset(Base):
    __tablename__ = "password_resets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    token = Column(String, unique=True, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())

    usuario = relationship("Usuario", back_populates="password_resets")

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
    limite_aprovado = Column(Numeric(12, 2), nullable=True, default=1000000.0) 
    limite_disponivel = Column(Numeric(12, 2), nullable=True, default=1000000.0)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    usuario = relationship("Usuario", back_populates="tomadores")

    propostas = relationship("Proposta", back_populates="tomador")
    asaas_cliente = relationship("ClienteAsaas", back_populates="tomador", uselist=False)
    representantes_legais = relationship("RepresentanteLegal", back_populates="tomador", cascade="all, delete-orphan")
    fiadores = relationship("Fiador", back_populates="tomador")
    ccg = relationship("CCG", back_populates="tomador", cascade="all, delete-orphan")

class RepresentanteLegal(Base):
    __tablename__ = "representantes_legais"

    id = Column(Integer, primary_key=True, index=True)
    tomador_id = Column(Integer, ForeignKey("tomadores.id", ondelete="CASCADE"), nullable=False)
    nome_completo = Column(String, nullable=False)
    cpf = Column(String, nullable=False)
    email = Column(String, nullable=False)

    # ✅ Novos campos
    endereco = Column(String, nullable=True)
    cidade = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    estado_civil = Column(String(50), nullable=True)
    profissao = Column(String(100), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    tomador = relationship("Tomador", back_populates="representantes_legais")


class Fiador(Base):
    __tablename__ = "fiadores"

    id = Column(Integer, primary_key=True, index=True)
    nome_completo = Column(String(255), nullable=False)
    cpf_cnpj = Column(String(20), nullable=False, unique=True)
    email = Column(String(255), nullable=False)
    tipo = Column(String(2), nullable=False)  # "PF" ou "PJ"
    tomador_id = Column(Integer, ForeignKey("tomadores.id", ondelete="CASCADE"), nullable=False)

    endereco = Column(String, nullable=True)
    cidade = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    estado_civil = Column(String(50), nullable=True)
    profissao = Column(String(100), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    tomador = relationship("Tomador", back_populates="fiadores")
    

class CCG(Base):
    __tablename__ = "ccg"

    id = Column(Integer, primary_key=True, index=True)
    tomador_id = Column(Integer, ForeignKey("tomadores.id"))
    caminho_pdf = Column(Text, nullable=True)
    d4sign_uuid = Column(String(100), nullable=True)
    d4sign_link = Column(Text, nullable=True)
    status = Column(String(50), default="gerando")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    tomador = relationship("Tomador", back_populates="ccg")

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
    tipo_emp = Column(String(50))
    # Financeiro
    taxa_percentual = Column(Numeric(5, 2), nullable=False, default=Decimal("5.00"))
    comissao_percentual = Column(Numeric(5, 2), nullable=False, default=Decimal("20.00"))
    premio = Column(Numeric(12, 2), nullable=True)
    comissao_valor = Column(Numeric(12, 2), nullable=True)

    # Dados da etapa de risco
    numero_contrato = Column(String(50), nullable=True)
    edital_processo = Column(String(300), nullable=True)
    percentual = Column(Numeric(5, 2), nullable=True)
    text_modelo = Column(String(700), nullable=True)
    link_pagamento = Column(String, nullable=True)  
    pago_em = Column(DateTime, nullable=True) 
    valor_pago = Column(Numeric(10, 2), nullable=True) 

    xml = Column(Text, nullable=True)

    # Relações  
    tomador_id = Column(Integer, ForeignKey("tomadores.id"))
    segurado_id = Column(Integer, ForeignKey("segurados.id"))
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario_adicional_id = Column(Integer, nullable=True)

    tomador = relationship("Tomador", back_populates="propostas")
    segurado = relationship("Segurado", back_populates="propostas")
    apolice = relationship("Apolice", uselist=False, back_populates="proposta")
    usuario = relationship("Usuario", back_populates="propostas")

class Apolice(Base):
    __tablename__ = "apolices"
    
    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(50), unique=True, nullable=False)
    data_criacao = Column(Date, default=datetime.utcnow)
    
    # PDF final assinado (em bytes)
    pdf_assinado = Column(LargeBinary, nullable=True)

    # ID do documento no D4Sign
    d4sign_document_id = Column(String(100), nullable=True)
    status_assinatura = Column(String(20), default="pendente")  

    # Relacionamento com proposta
    proposta_id = Column(Integer, ForeignKey("propostas.id"))
    proposta = relationship("Proposta", back_populates="apolice")



class ClienteAsaas(Base):
    __tablename__ = "clientes_asaas"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True, nullable=False)  # ID retornado pelo Asaas
    tomador_id = Column(Integer, ForeignKey("tomadores.id"), nullable=False)

    # Relacionamento
    tomador = relationship("Tomador", back_populates="asaas_cliente")


class Finance(Base):
    __tablename__ = "finances"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=True)
    criado_em = Column(DateTime, default=datetime.utcnow)

    usuarios = relationship("Usuario", back_populates="finance")
    corretoras = relationship("Corretora", back_populates="finance")
    assessorias = relationship("Assessoria", back_populates="finance")


class Corretora(Base):
    __tablename__ = "corretoras"

    id = Column(Integer, primary_key=True, index=True)
    finance_id = Column(Integer, ForeignKey("finances.id"), nullable=True)

    cnpj = Column(String(18), unique=True, nullable=False)
    razao_social = Column(String(255), nullable=False)
    inscricao_municipal = Column(String(50), nullable=True)
    comissao = Column(Numeric(5, 2), default=0.0)
    situacao_cnpj = Column(String(50), nullable=True)
    codigo_cnae = Column(String(20), nullable=True)
    ramo = Column(String(100), nullable=True)
    data_registro = Column(Date, nullable=True)
    data_recadastro = Column(Date, nullable=True)
    data_expiracao = Column(Date, nullable=True)
    telefone = Column(String(50), nullable=True)
    susep = Column(Integer, nullable=True)
    # Endereço
    cep = Column(String(20), nullable=True)
    endereco = Column(String(255), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(255), nullable=True)
    bairro = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    cidade = Column(String(100), nullable=True)

    # Dados bancários
    banco = Column(String(100), nullable=True)
    tipo_conta = Column(String(50), nullable=True)
    agencia = Column(String(20), nullable=True)
    digito_agencia = Column(String(5), nullable=True)
    conta = Column(String(20), nullable=True)
    digito_conta = Column(String(5), nullable=True)
    pix = Column(String, nullable=True)

    # Relacionamentos
    finance = relationship("Finance", back_populates="corretoras")
    usuarios = relationship("Usuario", back_populates="corretora")
    socios = relationship("SocioCorretora", back_populates="corretora")
    responsavel = relationship("ResponsavelFinanceiroCorretora", back_populates="corretora", uselist=False)
    documentos = relationship("DocumentoCorretora", back_populates="corretora")



class Assessoria(Base):
    __tablename__ = "assessorias"

    id = Column(Integer, primary_key=True, index=True)
    finance_id = Column(Integer, ForeignKey("finances.id"), nullable=False)

    cnpj = Column(String(18), unique=True, nullable=False)
    razao_social = Column(String(255), nullable=False)
    comissao = Column(Numeric(5, 2), default=0.0)  # % sobre produção dos corretores
    telefone = Column(String(20), nullable=True)
    data_registro = Column(Date, nullable=True)
    data_recadastro = Column(Date, nullable=True)
    data_expiracao = Column(Date, nullable=True)

    # Endereço
    cep = Column(String(20), nullable=True)
    endereco = Column(String(255), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(255), nullable=True)
    bairro = Column(String(100), nullable=True)
    uf = Column(String(2), nullable=True)
    cidade = Column(String(100), nullable=True)

    # Relacionamentos
    finance = relationship("Finance", back_populates="assessorias")
    usuarios = relationship("Usuario", back_populates="assessoria")
    documentos = relationship("DocumentoAssessoria", back_populates="assessoria")


class SocioCorretora(Base):
    __tablename__ = "socios_corretora"
    id = Column(Integer, primary_key=True, index=True)
    corretora_id = Column(Integer, ForeignKey("corretoras.id"))
    nome = Column(String(100), nullable=False)
    cpf = Column(String(14), nullable=False)
    corretora = relationship("Corretora", back_populates="socios")

class DocumentoAssessoria(Base):
    __tablename__ = "documentos_assessoria"
    id = Column(Integer, primary_key=True, index=True)
    assessoria_id = Column(Integer, ForeignKey("assessorias.id"))
    nome_arquivo = Column(String(255), nullable=False)
    caminho = Column(String(500), nullable=True)
    enviado_em = Column(DateTime, default=datetime.utcnow)
    assessoria = relationship("Assessoria", back_populates="documentos")


class ResponsavelFinanceiroCorretora(Base):
    __tablename__ = "responsaveis_financeiros_corretora"
    id = Column(Integer, primary_key=True, index=True)
    corretora_id = Column(Integer, ForeignKey("corretoras.id"))
    nome = Column(String(100), nullable=False)
    cpf = Column(String(14), nullable=False)
    email = Column(String(120), nullable=False)
    telefone = Column(String(20), nullable=True)
    corretora = relationship("Corretora", back_populates="responsavel")


class DocumentoCorretora(Base):
    __tablename__ = "documentos_corretora"
    id = Column(Integer, primary_key=True, index=True)
    corretora_id = Column(Integer, ForeignKey("corretoras.id"))
    nome_arquivo = Column(String(255), nullable=False)
    caminho = Column(String(500), nullable=True)
    enviado_em = Column(DateTime, default=datetime.utcnow)
    corretora = relationship("Corretora", back_populates="documentos")


class DocumentosTomador(Base):
    __tablename__ = "documentos_tomadores"

    id = Column(Integer, primary_key=True, index=True)
    tomador_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)

    contrato_social = Column(JSON, nullable=True)
    ultimas_alteracoes = Column(JSON, nullable=True)
    balanco = Column(JSON, nullable=True)
    ultimas_alteracoes_adicional = Column(JSON, nullable=True)
    dre = Column(JSON, nullable=True)
    balancete = Column(JSON, nullable=True)
    valor= Column(Numeric(12, 2), nullable=True) 

    status = Column(String(50), nullable=False, default="pendente")

    data_upload = Column(DateTime(timezone=True), default=func.now())


class Comissao(Base):
    __tablename__ = "comissoes"

    id = Column(Integer, primary_key=True, index=True)
    apolice_id = Column(Integer, ForeignKey("apolices.id", ondelete="CASCADE"), nullable=False)
    corretor_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"))
    assessoria_id = Column(Integer, ForeignKey("assessorias.id", ondelete="SET NULL"))

    valor_premio = Column(Numeric(12, 2), default=0)
    percentual_corretor = Column(Numeric(5, 2), default=0)
    valor_corretor = Column(Numeric(12, 2), default=0)
    percentual_assessoria = Column(Numeric(5, 2), default=0)
    valor_assessoria = Column(Numeric(12, 2), default=0)

    status_pagamento_corretor = Column(String(20), default="pendente")
    status_pagamento_assessoria = Column(String(20), default="pendente")
    data_pagamento_corretor = Column(Date)
    data_pagamento_assessoria = Column(Date)

    observacao = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relações
    apolice = relationship("Apolice", back_populates="comissoes")
    corretor = relationship("Usuario", foreign_keys=[corretor_id])
    assessoria = relationship("Assessoria", foreign_keys=[assessoria_id])
    pagamentos = relationship("PagamentoComissao", back_populates="comissao", cascade="all, delete-orphan")


class PagamentoComissao(Base):
    __tablename__ = "pagamentos_comissao"

    id = Column(Integer, primary_key=True, index=True)
    comissao_id = Column(Integer, ForeignKey("comissoes.id", ondelete="CASCADE"), nullable=False)
    tipo = Column(String(20), CheckConstraint("tipo IN ('corretor', 'assessoria')"))
    valor_pago = Column(Numeric(12, 2), nullable=False)
    data_pagamento = Column(Date, server_default=func.now())
    comprovante_url = Column(Text)
    observacao = Column(Text)

    comissao = relationship("Comissao", back_populates="pagamentos")