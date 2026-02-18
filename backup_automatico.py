"""
Script de Backup Automático do Banco de Dados
Para ser executado pelo Task Scheduler do Windows
"""
import shutil
from datetime import datetime
import os
import sys

# Fix encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def fazer_backup():
    """Cria backup do banco de dados"""
    
    # Obtém o diretório do script (não o diretório atual)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Caminhos relativos ao diretório do script
    db_path = os.path.join(script_dir, "database", "absenteismo.db")
    backup_dir = os.path.join(script_dir, "backups")
    
    # Verifica se o banco existe
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        print("   O sistema ainda não foi usado ou o arquivo foi movido.")
        return False
    
    # Cria pasta de backups
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nome do backup com data/hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"auto_absenteismo_backup_{timestamp}.db")
    
    try:
        # Copia o banco
        shutil.copy2(db_path, backup_path)
        
        # Tamanho do arquivo
        tamanho_mb = os.path.getsize(backup_path) / 1024 / 1024
        
        # Limpa backups antigos (mantém apenas últimos 7 dias)
        limpar_backups_antigos(backup_dir, dias=7)
        
        # Log do sucesso
        log_path = os.path.join(script_dir, "logs", "backup.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Backup criado: {backup_path} ({tamanho_mb:.2f} MB)\n")
        
        print("=" * 60)
        print("✅ BACKUP AUTOMÁTICO CRIADO COM SUCESSO!")
        print("=" * 60)
        print(f"📁 Arquivo: {backup_path}")
        print(f"📊 Tamanho: {tamanho_mb:.2f} MB")
        print(f"🕒 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        # Log do erro
        log_path = os.path.join(script_dir, "logs", "backup.log")
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ERRO: {str(e)}\n")
        
        print(f"❌ Erro ao criar backup: {e}")
        import traceback
        traceback.print_exc()
        return False

def limpar_backups_antigos(backup_dir, dias=7):
    """Remove backups mais antigos que o número de dias especificado"""
    from datetime import timedelta
    
    try:
        cutoff_date = datetime.now() - timedelta(days=dias)
        
        backups_removidos = 0
        for file in os.listdir(backup_dir):
            if file.endswith('.db') and 'backup' in file:
                file_path = os.path.join(backup_dir, file)
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                if file_time < cutoff_date:
                    try:
                        os.remove(file_path)
                        backups_removidos += 1
                        print(f"🗑️ Backup antigo removido: {file}")
                    except Exception as e:
                        print(f"⚠️ Erro ao remover backup antigo {file}: {e}")
        
        if backups_removidos > 0:
            print(f"✅ {backups_removidos} backup(s) antigo(s) removido(s)")
            
    except Exception as e:
        print(f"⚠️ Erro ao limpar backups antigos: {e}")

if __name__ == "__main__":
    print("\n💾 BACKUP AUTOMÁTICO DO BANCO DE DADOS\n")
    sucesso = fazer_backup()
    sys.exit(0 if sucesso else 1)

