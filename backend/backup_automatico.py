"""
Sistema de Backup Automático do Banco de Dados
Suporta backup diário, retenção configurável e notificações
"""
import os
import shutil
import schedule
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from .logger import app_logger, error_logger, log_operation

# Configurações
BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database")
DB_FILE = os.path.join(DB_DIR, "absenteismo.db")
RETENTION_DAYS = 7  # Manter últimos 7 dias de backup
MAX_BACKUPS = 30  # Máximo de backups a manter

# Fix encoding para Windows (apenas quando executado diretamente)
import sys
if sys.platform == 'win32' and hasattr(sys.stdout, 'buffer'):
    try:
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except (AttributeError, TypeError):
        # Já está configurado ou não é necessário
        pass


def criar_backup() -> Optional[str]:
    """
    Cria backup do banco de dados
    
    Returns:
        Caminho do arquivo de backup criado ou None em caso de erro
    """
    start_time = datetime.now()
    
    try:
        # Garante que o diretório de backups existe
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Verifica se o banco existe
        if not os.path.exists(DB_FILE):
            app_logger.warning("Banco de dados não encontrado para backup")
            return None
        
        # Nome do arquivo de backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"absenteismo_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_filename)
        
        # Cria backup
        shutil.copy2(DB_FILE, backup_path)
        
        # Verifica se o backup foi criado corretamente
        if not os.path.exists(backup_path):
            raise Exception("Backup não foi criado corretamente")
        
        file_size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        # Log de sucesso
        app_logger.info(f"Backup criado: {backup_filename} ({file_size_mb:.2f} MB) em {duration_ms:.2f}ms")
        log_operation(
            operation='backup_database',
            status='success',
            duration_ms=duration_ms,
            details={
                'backup_file': backup_filename,
                'size_mb': round(file_size_mb, 2)
            }
        )
        
        return backup_path
        
    except Exception as e:
        duration_ms = (datetime.now() - start_time).total_seconds() * 1000
        error_logger.error(f"Erro ao criar backup: {str(e)}", exc_info=True)
        log_operation(
            operation='backup_database',
            status='failed',
            duration_ms=duration_ms,
            details={'error': str(e)}
        )
        return None


def limpar_backups_antigos():
    """
    Remove backups antigos baseado em retenção e limite máximo
    """
    try:
        if not os.path.exists(BACKUP_DIR):
            return
        
        # Lista todos os backups
        backups = []
        for file in os.listdir(BACKUP_DIR):
            if file.startswith("absenteismo_backup_") and file.endswith(".db"):
                file_path = os.path.join(BACKUP_DIR, file)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                backups.append((file_path, mod_time, file))
        
        # Ordena por data (mais recente primeiro)
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # Remove backups mais antigos que RETENTION_DAYS
        cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
        removed_count = 0
        
        for file_path, mod_time, filename in backups:
            if mod_time < cutoff_date:
                try:
                    os.remove(file_path)
                    removed_count += 1
                    app_logger.info(f"Backup antigo removido: {filename}")
                except Exception as e:
                    app_logger.warning(f"Erro ao remover backup antigo {filename}: {e}")
        
        # Se ainda houver mais que MAX_BACKUPS, remove os mais antigos
        remaining_backups = [b for b in backups if b[1] >= cutoff_date]
        if len(remaining_backups) > MAX_BACKUPS:
            to_remove = remaining_backups[MAX_BACKUPS:]
            for file_path, _, filename in to_remove:
                try:
                    os.remove(file_path)
                    removed_count += 1
                    app_logger.info(f"Backup excedente removido: {filename}")
                except Exception as e:
                    app_logger.warning(f"Erro ao remover backup excedente {filename}: {e}")
        
        if removed_count > 0:
            app_logger.info(f"Limpeza de backups: {removed_count} arquivo(s) removido(s)")
        
    except Exception as e:
        error_logger.error(f"Erro ao limpar backups antigos: {str(e)}", exc_info=True)


def backup_periodico():
    """
    Executa backup e limpeza de backups antigos
    """
    app_logger.info("Iniciando backup periódico automático...")
    criar_backup()
    limpar_backups_antigos()
    app_logger.info("Backup periódico concluído")


def iniciar_backup_automatico():
    """
    Inicia o sistema de backup automático em thread separada
    """
    try:
        # Agenda backup diário às 02:00
        schedule.every().day.at("02:00").do(backup_periodico)
        
        # Também agenda backup imediato na inicialização (se não houver backup hoje)
        hoje = datetime.now().strftime("%Y%m%d")
        backups_hoje = [
            f for f in os.listdir(BACKUP_DIR) 
            if f.startswith(f"absenteismo_backup_{hoje}")
        ] if os.path.exists(BACKUP_DIR) else []
        
        if not backups_hoje:
            app_logger.info("Nenhum backup encontrado para hoje. Criando backup inicial...")
            criar_backup()
        
        # Thread para executar agendamentos
        def run_scheduler():
            while True:
                schedule.run_pending()
                import time
                time.sleep(60)  # Verifica a cada minuto
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        app_logger.info("Sistema de backup automático iniciado (backup diário às 02:00)")
        
    except Exception as e:
        error_logger.error(f"Erro ao iniciar backup automático: {str(e)}", exc_info=True)


def criar_backup_antes_operacao_critica(operacao: str) -> Optional[str]:
    """
    Cria backup antes de operação crítica (ex: upload, exclusão)
    
    Args:
        operacao: Nome da operação que requer backup
        
    Returns:
        Caminho do backup criado ou None
    """
    app_logger.info(f"Criando backup antes de operação crítica: {operacao}")
    backup_path = criar_backup()
    
    if backup_path:
        app_logger.info(f"Backup criado com sucesso antes de {operacao}")
    else:
        app_logger.warning(f"Falha ao criar backup antes de {operacao}")
    
    return backup_path

