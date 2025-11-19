"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "absenteismo.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine com pool de conexões otimizado
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    pool_size=10,  # Tamanho do pool de conexões
    max_overflow=20,  # Máximo de conexões extras
    pool_pre_ping=True,  # Verifica conexões antes de usar
    pool_recycle=3600  # Recicla conexões após 1 hora
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

def ensure_column(table_name: str, column_name: str, column_definition: str):
    """
    Ensure a column exists in a table, adding it if missing (SQLite only).
    
    SECURITY: Valida table_name e column_name para prevenir SQL injection.
    Estes valores são controlados internamente, mas validamos por segurança.
    """
    # Validação de segurança - apenas caracteres alfanuméricos e underscore
    import re
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', table_name):
        raise ValueError(f"Invalid table name: {table_name}")
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', column_name):
        raise ValueError(f"Invalid column name: {column_name}")
    # column_definition deve ser validado também
    if not re.match(r'^[A-Za-z0-9_()\s,]+$', column_definition):
        raise ValueError(f"Invalid column definition: {column_definition}")
    
    with engine.connect() as connection:
        # Usa text() com validação - SQLite não suporta parâmetros nomeados em DDL
        # Mas validamos os valores antes
        result = connection.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        if column_name not in columns:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))

def run_migrations():
    """Apply lightweight schema adjustments not covered by Base metadata."""
    ensure_column("clients", "logo_url", "VARCHAR(500)")
