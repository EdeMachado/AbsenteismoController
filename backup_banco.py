"""
Script de Backup do Banco de Dados
Cria backup automático do arquivo absenteismo.db
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
    
    # Caminhos
    db_path = os.path.join("database", "absenteismo.db")
    backup_dir = "backups"
    
    # Verifica se o banco existe
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado: {db_path}")
        print("   O sistema ainda não foi usado ou o arquivo foi movido.")
        return False
    
    # Cria pasta de backups
    os.makedirs(backup_dir, exist_ok=True)
    
    # Nome do backup com data/hora
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"absenteismo_backup_{timestamp}.db")
    
    try:
        # Copia o banco
        shutil.copy2(db_path, backup_path)
        
        # Tamanho do arquivo
        tamanho_mb = os.path.getsize(backup_path) / 1024 / 1024
        
        print("=" * 60)
        print("✅ BACKUP CRIADO COM SUCESSO!")
        print("=" * 60)
        print(f"📁 Arquivo: {backup_path}")
        print(f"📊 Tamanho: {tamanho_mb:.2f} MB")
        print(f"🕒 Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 60)
        print("\n💡 DICA: Guarde este arquivo para restaurar os dados depois!")
        print("   Para restaurar, copie este arquivo para: database/absenteismo.db")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        import traceback
        traceback.print_exc()
        return False

def listar_backups():
    """Lista todos os backups disponíveis"""
    backup_dir = "backups"
    
    if not os.path.exists(backup_dir):
        print("📁 Nenhum backup encontrado.")
        return
    
    backups = [f for f in os.listdir(backup_dir) if f.endswith('.db')]
    
    if not backups:
        print("📁 Nenhum backup encontrado.")
        return
    
    print("=" * 60)
    print("📦 BACKUPS DISPONÍVEIS:")
    print("=" * 60)
    
    backups.sort(reverse=True)  # Mais recente primeiro
    
    for i, backup in enumerate(backups[:10], 1):  # Mostra últimos 10
        backup_path = os.path.join(backup_dir, backup)
        tamanho_mb = os.path.getsize(backup_path) / 1024 / 1024
        data_modificacao = datetime.fromtimestamp(os.path.getmtime(backup_path))
        
        print(f"{i}. {backup}")
        print(f"   📊 {tamanho_mb:.2f} MB | 📅 {data_modificacao.strftime('%d/%m/%Y %H:%M:%S')}")
    
    if len(backups) > 10:
        print(f"\n... e mais {len(backups) - 10} backup(s)")
    
    print("=" * 60)

if __name__ == "__main__":
    print("\n💾 BACKUP DO BANCO DE DADOS - AbsenteismoController\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "listar":
        listar_backups()
    else:
        sucesso = fazer_backup()
        if sucesso:
            print("\n📋 Deseja ver os backups disponíveis? Execute:")
            print("   python backup_banco.py listar")
        sys.exit(0 if sucesso else 1)

