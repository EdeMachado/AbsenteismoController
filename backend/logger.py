"""
Sistema de Logging Estruturado - AbsenteismoController
Suporta auditoria LGPD, ISO 27001 e rastreabilidade completa
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Diretório de logs
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuração de níveis
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

class AuditLogger:
    """Logger especializado para auditoria (LGPD/ISO 27001)"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Handler para arquivo de auditoria
        audit_file = os.path.join(LOGS_DIR, "audit.log")
        handler = logging.handlers.RotatingFileHandler(
            audit_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=30,  # Mantém 30 arquivos de backup
            encoding='utf-8'
        )
        
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def log_access(self, user: str, action: str, resource: str, 
                   client_id: Optional[int] = None, ip: Optional[str] = None,
                   success: bool = True, details: Optional[Dict] = None):
        """
        Registra acesso a recursos (LGPD/ISO 27001)
        
        Args:
            user: Usuário que realizou a ação
            action: Ação realizada (CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT)
            resource: Recurso acessado (cliente, upload, atestado, etc.)
            client_id: ID do cliente (para isolamento LGPD)
            ip: IP do usuário
            success: Se a ação foi bem-sucedida
            details: Detalhes adicionais
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "action": action,
            "resource": resource,
            "client_id": client_id,
            "ip": ip,
            "success": success,
            "details": details or {}
        }
        
        message = json.dumps(log_data, ensure_ascii=False)
        
        if success:
            self.logger.info(f"AUDIT | {message}")
        else:
            self.logger.warning(f"AUDIT_FAILED | {message}")
    
    def log_data_access(self, user: str, client_id: int, data_type: str,
                       action: str, record_count: Optional[int] = None,
                       ip: Optional[str] = None):
        """Registra acesso a dados (crítico para LGPD)"""
        self.log_access(
            user=user,
            action=action,
            resource=f"{data_type} (client_id={client_id})",
            client_id=client_id,
            ip=ip,
            details={"data_type": data_type, "record_count": record_count}
        )
    
    def log_security_event(self, event_type: str, severity: str,
                          description: str, user: Optional[str] = None,
                          ip: Optional[str] = None, details: Optional[Dict] = None):
        """Registra eventos de segurança (ISO 27001)"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "severity": severity,
            "description": description,
            "user": user,
            "ip": ip,
            "details": details or {}
        }
        
        message = json.dumps(log_data, ensure_ascii=False)
        
        if severity == "CRITICAL":
            self.logger.critical(f"SECURITY | {message}")
        elif severity == "HIGH":
            self.logger.error(f"SECURITY | {message}")
        else:
            self.logger.warning(f"SECURITY | {message}")

# Instância global do audit logger
audit_logger = AuditLogger()

def setup_logging():
    """Configura sistema de logging completo"""
    
    # Logger principal da aplicação
    app_logger = logging.getLogger("app")
    app_logger.setLevel(getattr(logging, LOG_LEVEL))
    
    # Logger de erros
    error_logger = logging.getLogger("errors")
    error_logger.setLevel(logging.ERROR)
    
    # Logger de segurança
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.WARNING)
    
    # Formato padrão
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para app.log (rotação diária)
    app_file = os.path.join(LOGS_DIR, "app.log")
    app_handler = logging.handlers.TimedRotatingFileHandler(
        app_file,
        when='midnight',
        interval=1,
        backupCount=30,  # 30 dias
        encoding='utf-8'
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    app_logger.addHandler(app_handler)
    
    # Handler para errors.log
    error_file = os.path.join(LOGS_DIR, "errors.log")
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    error_logger.addHandler(error_handler)
    app_logger.addHandler(error_handler)  # App também escreve em errors
    
    # Handler para security.log
    security_file = os.path.join(LOGS_DIR, "security.log")
    security_handler = logging.handlers.RotatingFileHandler(
        security_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=30,  # 30 dias (importante para auditoria)
        encoding='utf-8'
    )
    security_handler.setLevel(logging.WARNING)
    security_handler.setFormatter(formatter)
    security_logger.addHandler(security_handler)
    
    # Console handler (apenas em desenvolvimento)
    if os.getenv("ENVIRONMENT", "production") == "development":
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        app_logger.addHandler(console_handler)
    
    # Evita propagação para root logger
    app_logger.propagate = False
    error_logger.propagate = False
    security_logger.propagate = False
    
    return app_logger, error_logger, security_logger

# Inicializa loggers
app_logger, error_logger, security_logger = setup_logging()

def get_logger(name: str = "app"):
    """Retorna logger configurado"""
    return logging.getLogger(name)

def log_operation(operation: str, user: Optional[str] = None,
                 client_id: Optional[int] = None, details: Optional[Dict] = None,
                 level: str = "INFO"):
    """
    Helper para logar operações com contexto LGPD
    
    Args:
        operation: Descrição da operação
        user: Usuário que realizou
        client_id: ID do cliente (para isolamento)
        details: Detalhes adicionais
        level: Nível do log (INFO, WARNING, ERROR)
    """
    log_data = {
        "operation": operation,
        "user": user,
        "client_id": client_id,
        "details": details or {}
    }
    
    message = f"{operation} | user={user} | client_id={client_id} | {json.dumps(details or {}, ensure_ascii=False)}"
    
    logger = get_logger()
    if level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)
    else:
        logger.info(message)
    
    # Se envolve dados de cliente, registra em auditoria
    if client_id is not None:
        audit_logger.log_access(
            user=user or "system",
            action=operation.split()[0].upper() if operation else "UNKNOWN",
            resource=operation,
            client_id=client_id,
            success=True
        )

