"""
Database models
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Client(Base):
    """Cliente/Empresa"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    
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
    
    # Dados do funcionário
    nome_funcionario = Column(String(200), nullable=True)
    cpf = Column(String(14), nullable=True)
    matricula = Column(String(50), nullable=True)
    setor = Column(String(100), nullable=True)
    cargo = Column(String(100), nullable=True)
    genero = Column(String(1), nullable=True)  # M/F
    
    # Dados do atestado
    data_afastamento = Column(Date, nullable=True)
    data_retorno = Column(Date, nullable=True)
    tipo_info_atestado = Column(Integer, nullable=True)  # 1=Dias, 3=Horas
    tipo_atestado = Column(String(50), nullable=True)  # Dias, Horas, etc
    cid = Column(String(10), nullable=True)
    descricao_cid = Column(String(500), nullable=True)
    
    # Métricas
    numero_dias_atestado = Column(Float, default=0)
    numero_horas_atestado = Column(Float, default=0)
    dias_perdidos = Column(Float, default=0)
    horas_perdidas = Column(Float, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    upload = relationship("Upload", back_populates="atestados")
