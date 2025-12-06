"""
Serviço de auditoria - histórico de alterações
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
from .models import AuditLog, User, Client
import json

class AuditService:
    """Serviço para registro de auditoria"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(
        self,
        action: str,
        resource_type: str,
        user_id: Optional[int] = None,
        client_id: Optional[int] = None,
        resource_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> AuditLog:
        """
        Registra uma ação no log de auditoria
        
        Args:
            action: Tipo de ação (CREATE, UPDATE, DELETE, VIEW, LOGIN, etc.)
            resource_type: Tipo de recurso (user, client, upload, atestado, etc.)
            user_id: ID do usuário que fez a ação
            client_id: ID da empresa afetada
            resource_id: ID do recurso afetado
            details: Dicionário com detalhes da alteração
            ip_address: IP do usuário
            user_agent: User agent do navegador
        
        Returns:
            AuditLog criado
        """
        log = AuditLog(
            user_id=user_id,
            client_id=client_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=json.dumps(details, ensure_ascii=False) if details else None,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now()
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_logs(
        self,
        user_id: Optional[int] = None,
        client_id: Optional[int] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list:
        """
        Busca logs de auditoria com filtros
        
        Returns:
            Lista de logs
        """
        query = self.db.query(AuditLog)
        
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if client_id:
            query = query.filter(AuditLog.client_id == client_id)
        if action:
            query = query.filter(AuditLog.action == action)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        
        logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
        
        result = []
        for log in logs:
            log_dict = {
                "id": log.id,
                "user_id": log.user_id,
                "user_name": log.user.username if log.user else None,
                "client_id": log.client_id,
                "client_name": log.client.nome if log.client else None,
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "details": json.loads(log.details) if log.details else None,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at.isoformat() if log.created_at else None
            }
            result.append(log_dict)
        
        return result
    
    def get_user_activity(self, user_id: int, limit: int = 50) -> list:
        """Busca atividades de um usuário"""
        return self.get_logs(user_id=user_id, limit=limit)
    
    def get_client_activity(self, client_id: int, limit: int = 50) -> list:
        """Busca atividades de uma empresa"""
        return self.get_logs(client_id=client_id, limit=limit)

