"""
Serviço de Notificações
Notifica eventos importantes: erros, backup, espaço em disco, etc.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

# Importa logger (com fallback)
try:
    from .logger import get_logger, security_logger
    logger = get_logger("notifications")
except ImportError:
    logger = None
    security_logger = None

class NotificationLevel(Enum):
    """Níveis de notificação"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class NotificationService:
    """Serviço de notificações"""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
        self.max_notifications = 100  # Mantém últimas 100
    
    def notify(
        self,
        level: NotificationLevel,
        title: str,
        message: str,
        details: Optional[Dict] = None,
        user: Optional[str] = None
    ):
        """
        Cria uma notificação
        
        Args:
            level: Nível da notificação
            title: Título
            message: Mensagem
            details: Detalhes adicionais
            user: Usuário relacionado
        """
        notification = {
            "id": len(self.notifications) + 1,
            "level": level.value,
            "title": title,
            "message": message,
            "details": details or {},
            "user": user,
            "timestamp": datetime.now().isoformat(),
            "read": False
        }
        
        self.notifications.append(notification)
        
        # Mantém apenas últimas N
        if len(self.notifications) > self.max_notifications:
            self.notifications = self.notifications[-self.max_notifications:]
        
        # Loga notificação crítica
        if level == NotificationLevel.CRITICAL:
            if security_logger:
                security_logger.critical(f"CRITICAL: {title} - {message}")
        elif level == NotificationLevel.ERROR:
            if logger:
                logger.error(f"ERROR: {title} - {message}")
        elif level == NotificationLevel.WARNING:
            if logger:
                logger.warning(f"WARNING: {title} - {message}")
        else:
            if logger:
                logger.info(f"INFO: {title} - {message}")
    
    def notify_backup_failed(self, error: str):
        """Notifica falha no backup"""
        self.notify(
            NotificationLevel.ERROR,
            "Backup Falhou",
            f"O backup automático falhou: {error}",
            {"type": "backup", "error": error}
        )
    
    def notify_backup_success(self, backup_path: str, size_mb: float):
        """Notifica sucesso no backup"""
        self.notify(
            NotificationLevel.INFO,
            "Backup Criado",
            f"Backup criado com sucesso: {size_mb:.2f} MB",
            {"type": "backup", "path": backup_path, "size_mb": size_mb}
        )
    
    def notify_disk_space_low(self, percent_free: float):
        """Notifica espaço em disco baixo"""
        level = NotificationLevel.CRITICAL if percent_free < 10 else NotificationLevel.WARNING
        self.notify(
            level,
            "Espaço em Disco Baixo",
            f"Apenas {percent_free:.1f}% de espaço livre no disco",
            {"type": "disk", "percent_free": percent_free}
        )
    
    def notify_integrity_issue(self, issue: str):
        """Notifica problema de integridade"""
        self.notify(
            NotificationLevel.ERROR,
            "Problema de Integridade",
            f"Problema detectado no banco de dados: {issue}",
            {"type": "integrity", "issue": issue}
        )
    
    def notify_security_event(self, event: str, severity: str, details: Optional[Dict] = None):
        """Notifica evento de segurança"""
        level_map = {
            "critical": NotificationLevel.CRITICAL,
            "high": NotificationLevel.ERROR,
            "medium": NotificationLevel.WARNING,
            "low": NotificationLevel.INFO
        }
        
        level = level_map.get(severity.lower(), NotificationLevel.WARNING)
        
        self.notify(
            level,
            "Evento de Segurança",
            event,
            {"type": "security", "severity": severity, **(details or {})}
        )
    
    def get_notifications(
        self,
        level: Optional[NotificationLevel] = None,
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Retorna notificações"""
        notifications = self.notifications.copy()
        
        # Filtra por nível
        if level:
            notifications = [n for n in notifications if n["level"] == level.value]
        
        # Filtra não lidas
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        # Ordena por timestamp (mais recente primeiro)
        notifications.sort(key=lambda x: x["timestamp"], reverse=True)
        
        # Limita
        return notifications[:limit]
    
    def mark_as_read(self, notification_id: int) -> bool:
        """Marca notificação como lida"""
        for notification in self.notifications:
            if notification["id"] == notification_id:
                notification["read"] = True
                return True
        return False
    
    def get_unread_count(self) -> int:
        """Retorna contagem de não lidas"""
        return sum(1 for n in self.notifications if not n["read"])

# Instância global
notification_service = NotificationService()








