"""
Script de Validação de Segurança
Verifica configurações de segurança do sistema
"""
import sys
import os

# Configura encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(__file__))

def verificar_secret_key():
    """Verifica se SECRET_KEY está configurada"""
    print("🔐 Verificando SECRET_KEY...")
    
    # Garante que .env foi carregado
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    secret_key = os.getenv("SECRET_KEY")
    
    if not secret_key:
        print("  ⚠️  SECRET_KEY não definida em variável de ambiente")
        print("     O sistema usará uma chave gerada automaticamente (não recomendado para produção)")
        return False
    else:
        if len(secret_key) < 32:
            print("  ⚠️  SECRET_KEY muito curta (recomendado: mínimo 32 caracteres)")
            return False
        else:
            print("  ✅ SECRET_KEY configurada corretamente")
            return True

def verificar_arquivo_env():
    """Verifica se arquivo .env existe"""
    print("\n📄 Verificando arquivo .env...")
    
    if os.path.exists(".env"):
        print("  ✅ Arquivo .env encontrado")
        
        # Verifica se .env está no .gitignore
        if os.path.exists(".gitignore"):
            with open(".gitignore", "r", encoding="utf-8") as f:
                gitignore_content = f.read()
                if ".env" in gitignore_content:
                    print("  ✅ Arquivo .env está no .gitignore")
                else:
                    print("  ⚠️  Arquivo .env NÃO está no .gitignore (deve ser ignorado!)")
        else:
            print("  ⚠️  Arquivo .gitignore não encontrado")
    else:
        print("  ⚠️  Arquivo .env não encontrado")
        print("     Crie um arquivo .env baseado em .env.example")

def verificar_imports_seguranca():
    """Verifica se imports de segurança estão corretos"""
    print("\n🔍 Verificando imports de segurança...")
    
    try:
        from backend.auth import SECRET_KEY
        print("  ✅ Módulo auth importado corretamente")
        
        # Verifica se SECRET_KEY não é a chave hardcoded antiga
        chave_hardcoded_antiga = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
        if SECRET_KEY == chave_hardcoded_antiga:
            print("  ❌ SECRET_KEY ainda está usando a chave hardcoded antiga!")
            return False
        else:
            print("  ✅ SECRET_KEY não é a chave hardcoded antiga")
            return True
    except Exception as e:
        print(f"  ❌ Erro ao importar módulo auth: {e}")
        return False

def verificar_validacao_client_id():
    """Verifica se função de validação de client_id existe"""
    print("\n🛡️  Verificando validação de client_id...")
    
    try:
        from backend.main import validar_client_id
        print("  ✅ Função validar_client_id encontrada")
        return True
    except Exception as e:
        print(f"  ❌ Função validar_client_id não encontrada: {e}")
        return False

def verificar_database_seguranca():
    """Verifica validações de segurança no database.py"""
    print("\n🗄️  Verificando segurança do database...")
    
    try:
        import re
        from backend.database import ensure_column
        
        # Testa validação com nome inválido
        try:
            ensure_column("'; DROP TABLE clients; --", "test", "VARCHAR(100)")
            print("  ❌ Validação de SQL injection não está funcionando!")
            return False
        except ValueError:
            print("  ✅ Validação de SQL injection funcionando")
            return True
    except Exception as e:
        print(f"  ⚠️  Não foi possível testar validação: {e}")
        return False

def verificar_logs():
    """Verifica se sistema de logs está configurado"""
    print("\n📝 Verificando sistema de logs...")
    
    logs_dir = "logs"
    if os.path.exists(logs_dir):
        print(f"  ✅ Diretório de logs existe: {logs_dir}")
        
        arquivos_log = ["app.log", "audit.log", "errors.log", "security.log"]
        for arquivo in arquivos_log:
            caminho = os.path.join(logs_dir, arquivo)
            if os.path.exists(caminho):
                tamanho = os.path.getsize(caminho)
                print(f"    ✅ {arquivo} existe ({tamanho} bytes)")
            else:
                print(f"    ⚠️  {arquivo} não existe (será criado automaticamente)")
    else:
        print(f"  ⚠️  Diretório de logs não existe: {logs_dir}")
        print("     Será criado automaticamente na primeira execução")

def main():
    """Função principal"""
    print("=" * 60)
    print("VALIDAÇÃO DE SEGURANÇA DO SISTEMA")
    print("=" * 60)
    
    resultados = []
    
    # Carrega variáveis de ambiente ANTES de importar outros módulos
    try:
        from dotenv import load_dotenv
        # Carrega explicitamente do arquivo .env na raiz
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
            print("\n✅ Variáveis de ambiente carregadas do .env")
        else:
            print("\n⚠️  Arquivo .env não encontrado")
    except ImportError:
        print("\n⚠️  python-dotenv não instalado (opcional)")
    except Exception as e:
        print(f"\n⚠️  Erro ao carregar .env: {e}")
    
    # Executa verificações
    resultados.append(("SECRET_KEY", verificar_secret_key()))
    verificar_arquivo_env()
    resultados.append(("Imports de Segurança", verificar_imports_seguranca()))
    resultados.append(("Validação client_id", verificar_validacao_client_id()))
    resultados.append(("Segurança Database", verificar_database_seguranca()))
    verificar_logs()
    
    # Resultado final
    print("\n" + "=" * 60)
    print("RESUMO DA VALIDAÇÃO")
    print("=" * 60)
    
    falhas = []
    for nome, resultado in resultados:
        status = "✅ PASSOU" if resultado else "❌ FALHOU"
        print(f"  {nome}: {status}")
        if not resultado:
            falhas.append(nome)
    
    print("=" * 60)
    
    if falhas:
        print(f"❌ {len(falhas)} verificação(ões) falharam:")
        for falha in falhas:
            print(f"   - {falha}")
        print("\n⚠️  Corrija os problemas antes de colocar em produção!")
        return 1
    else:
        print("✅ Todas as verificações passaram!")
        print("✅ Sistema pronto para produção")
        return 0

if __name__ == "__main__":
    sys.exit(main())

