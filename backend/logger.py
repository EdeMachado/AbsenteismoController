"""
Sistema de Logging Estruturado
Suporta auditoria, segurança e rastreabilidade (ISO 27001, LGPD)
"""
import logging
import logging.handlers
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Cria pasta de logs
LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Configuração de logs
LOG_FORMAT = '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Formato JSON para logs estruturados
class JSONFormatter(logging.Formatter):
    """Formatter que gera logs em formato JSON"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Adiciona campos extras se existirem
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'client_id'):
            log_data['client_id'] = record.client_id
        if hasattr(record, 'ip_address'):
            log_data['ip_address'] = record.ip_address
        if hasattr(record, 'action'):
            log_data['action'] = record.action
        if hasattr(record, 'resource'):
            log_data['resource'] = record.resource
        
        # Adiciona exception se houver
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(name: str, log_file: str, level: int = logging.INFO, 
                 use_json: bool = False, max_bytes: int = 10 * 1024 * 1024, 
                 backup_count: int = 5) -> logging.Logger:
    """
    Configura um logger com rotação de arquivos
    
    Args:
        name: Nome do logger
        log_file: Nome do arquivo de log
        level: Nível de log
        use_json: Se True, usa formato JSON
        max_bytes: Tamanho máximo do arquivo antes de rotacionar (padrão: 10MB)
        backup_count: Número de backups a manter
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove handlers existentes para evitar duplicação
    logger.handlers = []
    
    # Handler para arquivo com rotação
    log_path = os.path.join(LOGS_DIR, log_file)
    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    if use_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
    
    logger.addHandler(file_handler)
    
    # Handler para console (apenas em desenvolvimento)
    if os.getenv('ENVIRONMENT', 'development') == 'development':
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))
        logger.addHandler(console_handler)
    
    return logger


# Loggers principais
app_logger = setup_logger('app', 'app.log', logging.INFO)
error_logger = setup_logger('error', 'errors.log', logging.ERROR)
security_logger = setup_logger('security', 'security.log', logging.WARNING, use_json=True)
audit_logger = setup_logger('audit', 'audit.log', logging.INFO, use_json=True)


def log_audit(action: str, user_id: Optional[int] = None, 
              client_id: Optional[int] = None, resource: Optional[str] = None,
              ip_address: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
    """
    Registra ação de auditoria (ISO 27001, LGPD)
    
    Args:
        action: Ação realizada (ex: 'login', 'upload_file', 'delete_client')
        user_id: ID do usuário que realizou a ação
        client_id: ID do cliente afetado (se aplicável)
        resource: Recurso afetado (ex: 'client', 'upload', 'atestado')
        ip_address: IP de origem
        details: Detalhes adicionais da ação
    """
    # Campos reservados do LogRecord que não podem ser sobrescritos
    RESERVED_FIELDS = {'name', 'msg', 'args', 'created', 'filename', 'funcName', 
                      'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                      'message', 'pathname', 'process', 'processName', 'relativeCreated',
                      'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'}
    
    extra = {
        'action': action,
        'user_id': user_id,
        'client_id': client_id,
        'resource': resource,
        'ip_address': ip_address,
    }
    
    if details:
        # Filtra campos reservados do details
        for key, value in details.items():
            if key not in RESERVED_FIELDS:
                extra[key] = value
            else:
                # Renomeia campos reservados adicionando prefixo
                extra[f'ctx_{key}'] = value
    
    audit_logger.info(f"AUDIT: {action}", extra=extra)


def log_security(event: str, level: str = 'warning', 
                user_id: Optional[int] = None, ip_address: Optional[str] = None,
                details: Optional[Dict[str, Any]] = None):
    """
    Registra evento de segurança
    
    Args:
        event: Tipo de evento (ex: 'failed_login', 'rate_limit_exceeded', 'unauthorized_access')
        level: Nível de severidade ('info', 'warning', 'error', 'critical')
        user_id: ID do usuário (se aplicável)
        ip_address: IP de origem
        details: Detalhes adicionais
    """
    log_level = {
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }.get(level, logging.WARNING)
    
    extra = {
        'event': event,
        'user_id': user_id,
        'ip_address': ip_address,
    }
    
    if details:
        extra.update(details)
    
    security_logger.log(log_level, f"SECURITY: {event}", extra=extra)


def log_error(error: Exception, context: Optional[Dict[str, Any]] = None,
             user_id: Optional[int] = None, client_id: Optional[int] = None):
    """
    Registra erro com contexto
    
    Args:
        error: Exceção ocorrida
        context: Contexto adicional do erro
        user_id: ID do usuário (se aplicável)
        client_id: ID do cliente (se aplicável)
    """
    # Campos reservados do LogRecord que não podem ser sobrescritos
    RESERVED_FIELDS = {'name', 'msg', 'args', 'created', 'filename', 'funcName', 
                      'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                      'message', 'pathname', 'process', 'processName', 'relativeCreated',
                      'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'}
    
    extra = {}
    if user_id:
        extra['user_id'] = user_id
    if client_id:
        extra['client_id'] = client_id
    if context:
        # Filtra campos reservados do context
        for key, value in context.items():
            if key not in RESERVED_FIELDS:
                extra[key] = value
            else:
                # Renomeia campos reservados adicionando prefixo
                extra[f'ctx_{key}'] = value
    
    error_logger.error(
        f"ERROR: {type(error).__name__}: {str(error)}",
        exc_info=True,
        extra=extra
    )


# Função helper para logs de operações críticas
def log_operation(operation: str, status: str = 'success', 
                 duration_ms: Optional[float] = None,
                 user_id: Optional[int] = None, 
                 client_id: Optional[int] = None,
                 details: Optional[Dict[str, Any]] = None):
    """
    Registra operação do sistema
    
    Args:
        operation: Nome da operação
        status: 'success', 'failed', 'warning'
        duration_ms: Duração em milissegundos
        user_id: ID do usuário
        client_id: ID do cliente
        details: Detalhes adicionais
    """
    level = logging.INFO if status == 'success' else logging.WARNING
    
    message = f"OPERATION: {operation} | STATUS: {status}"
    if duration_ms:
        message += f" | DURATION: {duration_ms:.2f}ms"
    
    # Campos reservados do LogRecord que não podem ser sobrescritos
    RESERVED_FIELDS = {'name', 'msg', 'args', 'created', 'filename', 'funcName', 
                      'levelname', 'levelno', 'lineno', 'module', 'msecs', 
                      'message', 'pathname', 'process', 'processName', 'relativeCreated',
                      'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info'}
    
    extra = {
        'operation': operation,
        'status': status,
        'user_id': user_id,
        'client_id': client_id,
    }
    
    if duration_ms:
        extra['duration_ms'] = duration_ms
    if details:
        # Filtra campos reservados do details
        for key, value in details.items():
            if key not in RESERVED_FIELDS:
                extra[key] = value
            else:
                # Renomeia campos reservados adicionando prefixo
                extra[f'ctx_{key}'] = value
    
    app_logger.log(level, message, extra=extra)

