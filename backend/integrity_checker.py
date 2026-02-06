"""
Validador de Integridade do Banco de Dados
Verifica integridade, foreign keys e dados órfãos
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, List, Any
from .models import Client, Upload, Atestado

# Importa logger (com fallback)
try:
    from .logger import get_logger
    logger = get_logger("integrity")
except ImportError:
    logger = None

class IntegrityChecker:
    """Validador de integridade do banco"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_all(self) -> Dict[str, Any]:
        """
        Executa todas as verificações de integridade
        
        Returns:
            Dicionário com resultados de todas as verificações
        """
        results = {
            "overall_healthy": True,
            "checks": {}
        }
        
        # Verifica integridade do SQLite
        results["checks"]["sqlite_integrity"] = self.check_sqlite_integrity()
        
        # Verifica foreign keys
        results["checks"]["foreign_keys"] = self.check_foreign_keys()
        
        # Verifica dados órfãos
        results["checks"]["orphan_data"] = self.check_orphan_data()
        
        # Verifica isolamento de dados (LGPD)
        results["checks"]["data_isolation"] = self.check_data_isolation()
        
        # Determina saúde geral
        for check in results["checks"].values():
            if isinstance(check, dict) and not check.get("healthy", True):
                results["overall_healthy"] = False
        
        return results
    
    def check_sqlite_integrity(self) -> Dict[str, Any]:
        """Verifica integridade do SQLite"""
        try:
            result = self.db.execute(text("PRAGMA quick_check"))
            integrity = result.scalar()
            
            return {
                "healthy": integrity == "ok",
                "result": integrity,
                "message": "Integridade OK" if integrity == "ok" else f"Problema detectado: {integrity}"
            }
        except Exception as e:
            if logger:
                logger.error(f"Erro ao verificar integridade SQLite: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def check_foreign_keys(self) -> Dict[str, Any]:
        """Verifica integridade de foreign keys"""
        issues = []
        
        try:
            # Verifica atestados sem upload
            orphan_atestados = self.db.query(Atestado).outerjoin(Upload).filter(Upload.id == None).count()
            if orphan_atestados > 0:
                issues.append(f"{orphan_atestados} atestados sem upload associado")
            
            # Verifica uploads sem cliente
            orphan_uploads = self.db.query(Upload).outerjoin(Client).filter(Client.id == None).count()
            if orphan_uploads > 0:
                issues.append(f"{orphan_uploads} uploads sem cliente associado")
            
            return {
                "healthy": len(issues) == 0,
                "issues": issues,
                "message": "Foreign keys OK" if len(issues) == 0 else "; ".join(issues)
            }
        except Exception as e:
            if logger:
                logger.error(f"Erro ao verificar foreign keys: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def check_orphan_data(self) -> Dict[str, Any]:
        """Verifica dados órfãos"""
        issues = []
        
        try:
            # Verifica uploads sem atestados
            empty_uploads = self.db.query(Upload).outerjoin(Atestado).filter(Atestado.id == None).count()
            if empty_uploads > 0:
                issues.append(f"{empty_uploads} uploads sem atestados")
            
            return {
                "healthy": len(issues) == 0,
                "issues": issues,
                "message": "Sem dados órfãos" if len(issues) == 0 else "; ".join(issues)
            }
        except Exception as e:
            if logger:
                logger.error(f"Erro ao verificar dados órfãos: {e}")
            return {
                "healthy": False,
                "error": str(e)
            }
    
    def check_data_isolation(self) -> Dict[str, Any]:
        """
        Verifica isolamento de dados por client_id (LGPD)
        Garante que não há vazamento de dados entre clientes
        """
        issues = []
        
        try:
            # Verifica se todos os uploads têm client_id válido
            uploads_sem_client = self.db.query(Upload).filter(Upload.client_id == None).count()
            if uploads_sem_client > 0:
                issues.append(f"{uploads_sem_client} uploads sem client_id")
            
            # Verifica se todos os atestados estão vinculados a uploads com client_id
            atestados_sem_client = self.db.query(Atestado).join(Upload).filter(
                Upload.client_id == None
            ).count()
            if atestados_sem_client > 0:
                issues.append(f"{atestados_sem_client} atestados vinculados a uploads sem client_id")
            
            return {
                "healthy": len(issues) == 0,
                "issues": issues,
                "message": "Isolamento de dados OK (LGPD)" if len(issues) == 0 else "; ".join(issues),
                "lgpd_compliant": len(issues) == 0
            }
        except Exception as e:
            if logger:
                logger.error(f"Erro ao verificar isolamento de dados: {e}")
            return {
                "healthy": False,
                "error": str(e),
                "lgpd_compliant": False
            }

