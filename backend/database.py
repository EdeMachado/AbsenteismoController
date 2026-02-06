"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "absenteismo.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
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
    """Ensure a column exists in a table, adding it if missing (SQLite only)."""
    with engine.connect() as connection:
        result = connection.execute(text(f"PRAGMA table_info({table_name})"))
        columns = [row[1] for row in result]
        if column_name not in columns:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))

def run_migrations():
    """Apply lightweight schema adjustments not covered by Base metadata."""
    ensure_column("clients", "logo_url", "VARCHAR(500)")

def check_database_health(db: Session) -> dict:
    """
    Verifica saúde do banco de dados (com fallback seguro)
    Se qualquer verificação falhar, retorna status básico
    """
    from sqlalchemy import text
    
    health = {
        "healthy": True,
        "connected": False
    }
    
    try:
        # Testa conexão básica
        db.execute(text("SELECT 1"))
        health["connected"] = True
        
        # Tenta verificações extras (opcional)
        try:
            # Verifica integridade (SQLite) - pode ser lento, então opcional
            result = db.execute(text("PRAGMA quick_check"))
            integrity = result.scalar()
            health["integrity_check"] = integrity == "ok"
        except Exception:
            # Se falhar, ignora
            pass
        
        # Tenta verificar tamanho do banco
        try:
            import os
            if os.path.exists(DB_PATH):
                size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
                health["size_mb"] = round(size_mb, 2)
        except Exception:
            # Se falhar, ignora
            pass
            
    except Exception as e:
        # Se conexão falhar, marca como não saudável
        health["healthy"] = False
        health["connected"] = False
        health["error"] = "Connection failed"
    
    return health
