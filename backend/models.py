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
    logos = relationship("ClientLogo", back_populates="client", cascade="all, delete-orphan")

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
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)  # Empresa associada ao usuário
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    client = relationship("Client")
    
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

class ClientLogo(Base):
    """Logos de um cliente (suporte a múltiplos logos)"""
    __tablename__ = "client_logos"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    logo_url = Column(String(500), nullable=False)
    is_principal = Column(Boolean, default=False)  # Logo principal (usado por padrão)
    descricao = Column(String(200), nullable=True)  # Descrição opcional do logo
    created_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    client = relationship("Client", back_populates="logos")

class SavedFilter(Base):
    """Filtros salvos para acesso rápido"""
    __tablename__ = "saved_filters"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    nome = Column(String(100), nullable=False)  # Nome do filtro salvo
    mes_inicio = Column(String(7), nullable=True)  # YYYY-MM
    mes_fim = Column(String(7), nullable=True)  # YYYY-MM
    funcionarios = Column(Text, nullable=True)  # JSON array de funcionários
    setores = Column(Text, nullable=True)  # JSON array de setores
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User")
    client = relationship("Client")

class AuditLog(Base):
    """Log de auditoria - histórico de alterações"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Usuário que fez a ação
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)  # Empresa afetada
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, etc.
    resource_type = Column(String(50), nullable=False)  # user, client, upload, atestado, etc.
    resource_id = Column(Integer, nullable=True)  # ID do recurso afetado
    details = Column(Text, nullable=True)  # JSON com detalhes da alteração
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    user = relationship("User")
    client = relationship("Client")

class ReportSchedule(Base):
    """Agendamento de relatórios automáticos por email"""
    __tablename__ = "report_schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    nome = Column(String(200), nullable=False)  # Nome do relatório
    frequencia = Column(String(20), nullable=False)  # daily, weekly, monthly
    dia_semana = Column(Integer, nullable=True)  # 0-6 (domingo-sábado) para weekly
    dia_mes = Column(Integer, nullable=True)  # 1-31 para monthly
    hora_envio = Column(String(5), nullable=False, default="08:00")  # HH:MM
    emails_destinatarios = Column(Text, nullable=False)  # JSON array de emails
    formato = Column(String(20), default="excel")  # excel, pdf, ambos
    incluir_graficos = Column(Boolean, default=True)
    periodo = Column(String(20), default="ultimo_mes")  # ultimo_mes, ultimos_3_meses, custom
    mes_inicio_custom = Column(String(7), nullable=True)  # YYYY-MM
    mes_fim_custom = Column(String(7), nullable=True)  # YYYY-MM
    is_active = Column(Boolean, default=True)
    ultimo_envio = Column(DateTime, nullable=True)
    proximo_envio = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    client = relationship("Client")

class Alert(Base):
    """Alertas e notificações do sistema"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    tipo = Column(String(50), nullable=False)  # limite_excedido, tendencia_alta, anomalia, etc.
    severidade = Column(String(20), default="medium")  # low, medium, high, critical
    titulo = Column(String(200), nullable=False)
    mensagem = Column(Text, nullable=False)
    dados = Column(Text, nullable=True)  # JSON com dados do alerta
    is_lido = Column(Boolean, default=False)
    is_resolvido = Column(Boolean, default=False)
    enviado_email = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now, index=True)
    lido_em = Column(DateTime, nullable=True)
    resolvido_em = Column(DateTime, nullable=True)
    
    # Relationships
    client = relationship("Client")

class AlertRule(Base):
    """Regras de alertas configuráveis"""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    nome = Column(String(200), nullable=False)
    tipo = Column(String(50), nullable=False)  # dias_perdidos, taxa_absenteismo, cid_frequente, etc.
    condicao = Column(String(20), nullable=False)  # maior_que, menor_que, igual, diferente
    valor_limite = Column(Float, nullable=False)
    periodo = Column(String(20), default="mensal")  # mensal, trimestral, anual
    enviar_email = Column(Boolean, default=True)
    emails_destinatarios = Column(Text, nullable=True)  # JSON array de emails
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    client = relationship("Client")

class ColaboradorINSS(Base):
    """Colaboradores em acompanhamento INSS - Afastados, Retornando e Aposentados por Invalidez"""
    __tablename__ = "colaboradores_inss"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    
    # Campos da planilha INSS
    cont = Column(String(50), nullable=True)  # CONT
    re = Column(String(50), nullable=True)  # RE
    nome = Column(String(200), nullable=True)  # NOME
    id_colaborador = Column(String(50), nullable=True)  # ID
    setor = Column(String(100), nullable=True)  # SETOR
    funcao = Column(String(100), nullable=True)  # FUNÇÃO
    data_de_afast = Column(Date, nullable=True)  # DATA DE AFAST.
    acid_trab = Column(String(50), nullable=True)  # ACID. TRAB.
    cid10 = Column(String(20), nullable=True)  # CID10
    inicio_do_inss = Column(Date, nullable=True)  # INÍCIO DO INSS
    fim_do_beneficio = Column(Date, nullable=True)  # FIM DO BENÉFICIO
    motivo = Column(String(200), nullable=True)  # MOTIVO
    parecer_medico = Column(Text, nullable=True)  # PARECER MÉDICO
    
    # Dados originais da planilha (JSON com todas as colunas)
    dados_originais = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    client = relationship("Client")