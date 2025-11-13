"""
Database models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Client(Base):
    """Cliente/Empresa"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)  # Razão Social
    cnpj = Column(String(18), unique=True, nullable=True)
    nome_fantasia = Column(String(200), nullable=True)
    inscricao_estadual = Column(String(20), nullable=True)
    inscricao_municipal = Column(String(20), nullable=True)
    cep = Column(String(10), nullable=True)
    endereco = Column(String(300), nullable=True)
    numero = Column(String(20), nullable=True)
    complemento = Column(String(100), nullable=True)
    bairro = Column(String(100), nullable=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(String(2), nullable=True)
    telefone = Column(String(20), nullable=True)
    email = Column(String(200), nullable=True)
    situacao = Column(String(50), nullable=True)  # ATIVA, BAIXADA, etc.
    data_abertura = Column(Date, nullable=True)
    atividade_principal = Column(String(500), nullable=True)
    logo_url = Column(String(500), nullable=True)
    cores_personalizadas = Column(Text, nullable=True)  # JSON com paleta de cores personalizada
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    uploads = relationship("Upload", back_populates="client", cascade="all, delete-orphan")

class Upload(Base):
    """Upload de planilha mensal"""
    __tablename__ = "uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    mes_referencia = Column(String(7), nullable=False)  # YYYY-MM
    data_upload = Column(DateTime, default=datetime.now)
    total_registros = Column(Integer, default=0)
    
    # Relationships
    client = relationship("Client", back_populates="uploads")
    atestados = relationship("Atestado", back_populates="upload", cascade="all, delete-orphan")

class Atestado(Base):
    """Registro de atestado"""
    __tablename__ = "atestados"
    
    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"), nullable=False)
    
    # Campos da planilha padronizada
    nomecompleto = Column(String(200), nullable=True)  # NOMECOMPLETO
    descricao_atestad = Column(String(500), nullable=True)  # DESCRIÇÃO ATESTAD
    dias_atestados = Column(Float, default=0)  # DIAS ATESTADOS
    cid = Column(String(10), nullable=True)  # CID
    diagnostico = Column(String(500), nullable=True)  # DIAGNÓSTICO
    centro_custo = Column(String(100), nullable=True)  # CENTROCUST
    setor = Column(String(100), nullable=True)  # setor
    motivo_atestado = Column(String(200), nullable=True)  # motivo atestado
    escala = Column(String(50), nullable=True)  # escala
    horas_dia = Column(Float, default=0)  # Horas/dia
    horas_perdi = Column(Float, default=0)  # Horas perdi
    
    # Campos legados (para compatibilidade)
    nome_funcionario = Column(String(200), nullable=True)
    cpf = Column(String(14), nullable=True)
    matricula = Column(String(50), nullable=True)
    cargo = Column(String(100), nullable=True)
    genero = Column(String(1), nullable=True)
    data_afastamento = Column(Date, nullable=True)
    data_retorno = Column(Date, nullable=True)
    tipo_info_atestado = Column(Integer, nullable=True)
    tipo_atestado = Column(String(50), nullable=True)
    descricao_cid = Column(String(500), nullable=True)
    numero_dias_atestado = Column(Float, default=0)
    numero_horas_atestado = Column(Float, default=0)
    dias_perdidos = Column(Float, default=0)
    horas_perdidas = Column(Float, default=0)
    
    # Dados originais da planilha (JSON com todas as colunas)
    dados_originais = Column(Text, nullable=True)  # JSON com todas as colunas originais
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    upload = relationship("Upload", back_populates="atestados")

class User(Base):
    """Usuário do sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(200), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    nome_completo = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
class Config(Base):
    """Configurações do sistema"""
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True)
    chave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=True)
    descricao = Column(String(500), nullable=True)
    tipo = Column(String(50), default="string")  # string, number, boolean, json
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class ClientColumnMapping(Base):
    """Mapeamento de colunas da planilha por cliente"""
    __tablename__ = "client_column_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, unique=True)
    
    # Mapeamento de colunas da planilha para campos do sistema (JSON)
    # Exemplo: {"NOMECOMPLETO": "nomecompleto", "SETOR_EMPRESA": "setor", ...}
    column_mapping = Column(Text, nullable=False)  # JSON com mapeamento
    
    # Configurações de gráficos personalizados (JSON)
    graficos_configurados = Column(Text, nullable=True)  # JSON com array de gráficos
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    client = relationship("Client")

class Produtividade(Base):
    """Dados de produtividade por tipo de consulta"""
    __tablename__ = "produtividade"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    mes_referencia = Column(String(7), nullable=False)  # YYYY-MM
    
    # Tipo de consulta (número e descrição)
    numero_tipo = Column(String(50), nullable=False)  # Ex: "1", "2", "Tipo A", etc.
    tipo_consulta = Column(String(200), nullable=True)  # Descrição do tipo
    
    # Valores por categoria
    ocupacionais = Column(Integer, default=0)
    assistenciais = Column(Integer, default=0)
    acidente_trabalho = Column(Integer, default=0)
    inss = Column(Integer, default=0)
    sinistralidade = Column(Integer, default=0)
    absenteismo = Column(Integer, default=0)
    pericia_indireta = Column(Integer, default=0)
    total = Column(Integer, default=0)  # Soma automática
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    client = relationship("Client")
