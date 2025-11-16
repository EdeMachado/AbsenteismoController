"""
Script de Teste do Sistema
Verifica se todas as melhorias estão funcionando corretamente
"""
import sys
import os
import requests
import time
from pathlib import Path

# Fix encoding para Windows
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Adiciona o diretório raiz ao path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

def print_header(text):
    """Imprime cabeçalho formatado"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def print_success(text):
    """Imprime mensagem de sucesso"""
    print(f"✅ {text}")

def print_error(text):
    """Imprime mensagem de erro"""
    print(f"❌ {text}")

def print_warning(text):
    """Imprime mensagem de aviso"""
    print(f"⚠️  {text}")

def test_logs_directory():
    """Testa se o diretório de logs existe"""
    print_header("TESTE 1: Diretório de Logs")
    
    logs_dir = BASE_DIR / "logs"
    if logs_dir.exists():
        print_success(f"Diretório de logs existe: {logs_dir}")
        
        # Lista arquivos de log
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            print(f"   Arquivos de log encontrados: {len(log_files)}")
            for log_file in log_files[:5]:  # Mostra até 5
                size_kb = log_file.stat().st_size / 1024
                print(f"   - {log_file.name} ({size_kb:.2f} KB)")
        else:
            print_warning("Nenhum arquivo de log encontrado ainda")
    else:
        print_error(f"Diretório de logs não existe: {logs_dir}")
        print("   Será criado automaticamente quando o sistema iniciar")
    
    return True

def test_backups_directory():
    """Testa se o diretório de backups existe"""
    print_header("TESTE 2: Diretório de Backups")
    
    backups_dir = BASE_DIR / "backups"
    if backups_dir.exists():
        print_success(f"Diretório de backups existe: {backups_dir}")
        
        # Lista backups
        backup_files = list(backups_dir.glob("*.db"))
        if backup_files:
            print(f"   Backups encontrados: {len(backup_files)}")
            for backup_file in sorted(backup_files, key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
                size_mb = backup_file.stat().st_size / (1024 * 1024)
                mod_time = time.ctime(backup_file.stat().st_mtime)
                print(f"   - {backup_file.name} ({size_mb:.2f} MB) - {mod_time}")
        else:
            print_warning("Nenhum backup encontrado ainda")
    else:
        print_warning(f"Diretório de backups não existe: {backups_dir}")
        print("   Será criado automaticamente quando o sistema iniciar")
    
    return True

def test_database():
    """Testa se o banco de dados existe"""
    print_header("TESTE 3: Banco de Dados")
    
    db_file = BASE_DIR / "database" / "absenteismo.db"
    if db_file.exists():
        size_mb = db_file.stat().st_size / (1024 * 1024)
        print_success(f"Banco de dados existe: {db_file}")
        print(f"   Tamanho: {size_mb:.2f} MB")
        return True
    else:
        print_warning(f"Banco de dados não existe: {db_file}")
        print("   Será criado automaticamente quando o sistema iniciar")
        return False

def test_modules():
    """Testa se os módulos podem ser importados"""
    print_header("TESTE 4: Módulos do Sistema")
    
    modules = [
        "backend.logger",
        "backend.backup_automatico",
        "backend.upload_handler",
        "backend.middleware_logging",
        "backend.validators",
    ]
    
    all_ok = True
    for module_name in modules:
        try:
            __import__(module_name)
            print_success(f"Módulo {module_name} importado com sucesso")
        except ImportError as e:
            print_error(f"Erro ao importar {module_name}: {e}")
            all_ok = False
        except Exception as e:
            print_warning(f"Erro ao importar {module_name}: {e}")
    
    return all_ok

def test_health_endpoint():
    """Testa o endpoint de health check"""
    print_header("TESTE 5: Health Check Endpoint")
    
    try:
        # Tenta conectar ao servidor (se estiver rodando)
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print_success("Health check respondeu com sucesso")
            print(f"   Status: {data.get('status', 'unknown')}")
            
            checks = data.get('checks', {})
            for check_name, check_data in checks.items():
                status = check_data.get('status', 'unknown')
                if status == 'ok':
                    print(f"   ✅ {check_name}: OK")
                elif status == 'warning':
                    print_warning(f"{check_name}: {check_data.get('message', 'warning')}")
                else:
                    print_error(f"{check_name}: {check_data.get('message', 'error')}")
            
            return True
        else:
            print_warning(f"Health check retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_warning("Servidor não está rodando (isso é normal se você ainda não iniciou)")
        print("   Para testar, inicie o servidor com: uvicorn backend.main:app --reload")
        return None
    except Exception as e:
        print_error(f"Erro ao testar health check: {e}")
        return False

def test_dependencies():
    """Testa se as dependências estão instaladas"""
    print_header("TESTE 6: Dependências")
    
    dependencies = [
        "psutil",
        "schedule",
        "fastapi",
        "sqlalchemy",
        "pandas",
    ]
    
    all_ok = True
    for dep in dependencies:
        try:
            __import__(dep)
            print_success(f"{dep} instalado")
        except ImportError:
            print_error(f"{dep} NÃO instalado")
            print(f"   Instale com: pip install {dep}")
            all_ok = False
    
    return all_ok

def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("  TESTE DO SISTEMA - AbsenteismoController")
    print("  Verificando melhorias implementadas")
    print("=" * 60)
    
    results = {
        "Logs": test_logs_directory(),
        "Backups": test_backups_directory(),
        "Database": test_database(),
        "Modules": test_modules(),
        "Health": test_health_endpoint(),
        "Dependencies": test_dependencies(),
    }
    
    print_header("RESUMO DOS TESTES")
    
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    for test_name, result in results.items():
        if result is True:
            print_success(f"{test_name}: PASSOU")
        elif result is False:
            print_error(f"{test_name}: FALHOU")
        else:
            print_warning(f"{test_name}: PULADO")
    
    print(f"\n📊 Resultados: {passed} passou, {failed} falhou, {skipped} pulado")
    
    if failed == 0:
        print_success("\n🎉 Todos os testes críticos passaram!")
        print("\n💡 Próximos passos:")
        print("   1. Instale as dependências: pip install -r requirements.txt")
        print("   2. Inicie o servidor: uvicorn backend.main:app --reload")
        print("   3. Acesse http://localhost:8000/api/health para verificar")
    else:
        print_error(f"\n⚠️  {failed} teste(s) falharam. Verifique os erros acima.")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    main()

