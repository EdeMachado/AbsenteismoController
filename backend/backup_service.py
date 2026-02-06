"""
Serviço de Backup Automático do Banco de Dados
Backup diário automático com retenção configurável
"""
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import threading
import time

# Importa logger (com fallback)
try:
    from .logger import get_logger
    logger = get_logger("backup")
except ImportError:
    logger = None

class BackupService:
    """Serviço de backup automático"""
    
    def __init__(self, db_path: str, backup_dir: str = "backups"):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.retention_days = 7  # Mantém backups dos últimos 7 dias
        self.running = False
        self.thread = None
        
        # Cria diretório de backups
        os.makedirs(backup_dir, exist_ok=True)
    
    def create_backup(self, prefix: str = "auto") -> Optional[str]:
        """
        Cria backup do banco de dados
        
        Args:
            prefix: Prefixo do backup (auto, manual, etc.)
            
        Returns:
            Caminho do backup criado ou None se falhar
        """
        if not os.path.exists(self.db_path):
            if logger:
                logger.warning(f"Banco de dados não encontrado: {self.db_path}")
            return None
        
        try:
            # Nome do backup com timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"{prefix}_absenteismo_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Copia o banco
            shutil.copy2(self.db_path, backup_path)
            
            # Tamanho do backup
            size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            
            if logger:
                logger.info(f"Backup criado: {backup_filename} ({size_mb:.2f} MB)")
            
            # Limpa backups antigos
            self.clean_old_backups()
            
            return backup_path
            
        except Exception as e:
            if logger:
                logger.error(f"Erro ao criar backup: {e}")
            
            # Notifica falha (opcional)
            try:
                from .notification_service import notification_service
                notification_service.notify_backup_failed(str(e))
            except:
                pass
            
            return None
    
    def clean_old_backups(self):
        """Remove backups mais antigos que retention_days"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            
            for file in os.listdir(self.backup_dir):
                if file.endswith('.db') and 'backup' in file:
                    file_path = os.path.join(self.backup_dir, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_time < cutoff_date:
                        try:
                            os.remove(file_path)
                            if logger:
                                logger.info(f"Backup antigo removido: {file}")
                        except Exception as e:
                            if logger:
                                logger.warning(f"Erro ao remover backup antigo {file}: {e}")
        except Exception as e:
            if logger:
                logger.error(f"Erro ao limpar backups antigos: {e}")
    
    def start_auto_backup(self, interval_hours: int = 24):
        """
        Inicia backup automático em background
        
        Args:
            interval_hours: Intervalo entre backups em horas (padrão: 24h)
        """
        if self.running:
            if logger:
                logger.warning("Backup automático já está rodando")
            return
        
        self.running = True
        
        def backup_loop():
            while self.running:
                try:
                    # Cria backup
                    self.create_backup(prefix="auto")
                    
                    # Aguarda próximo backup
                    time.sleep(interval_hours * 3600)
                except Exception as e:
                    if logger:
                        logger.error(f"Erro no loop de backup: {e}")
                    # Aguarda 1 hora antes de tentar novamente
                    time.sleep(3600)
        
        self.thread = threading.Thread(target=backup_loop, daemon=True)
        self.thread.start()
        
        if logger:
            logger.info(f"Backup automático iniciado (intervalo: {interval_hours}h)")
    
    def stop_auto_backup(self):
        """Para backup automático"""
        self.running = False
        if logger:
            logger.info("Backup automático parado")
    
    def get_backup_list(self) -> list:
        """Retorna lista de backups disponíveis"""
        backups = []
        try:
            for file in os.listdir(self.backup_dir):
                if file.endswith('.db') and 'backup' in file:
                    file_path = os.path.join(self.backup_dir, file)
                    size_mb = os.path.getsize(file_path) / (1024 * 1024)
                    modified = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    backups.append({
                        "filename": file,
                        "size_mb": round(size_mb, 2),
                        "created": modified.isoformat(),
                        "path": file_path
                    })
            
            # Ordena por data (mais recente primeiro)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
        except Exception as e:
            if logger:
                logger.error(f"Erro ao listar backups: {e}")
        
        return backups

# Instância global (será inicializada no startup)
backup_service: Optional[BackupService] = None

def init_backup_service(db_path: str):
    """Inicializa serviço de backup"""
    global backup_service
    try:
        backup_service = BackupService(db_path)
        # Inicia backup automático diário
        backup_service.start_auto_backup(interval_hours=24)
        return backup_service
    except Exception as e:
        if logger:
            logger.error(f"Erro ao inicializar backup service: {e}")
        return None

