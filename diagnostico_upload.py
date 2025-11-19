#!/usr/bin/env python3
"""
Script de diagnóstico para identificar problemas no upload
Execute no servidor para testar cada etapa isoladamente
"""

import os
import sys
sys.path.insert(0, '/var/www/absenteismo')

def testar_imports():
    """Testa se todos os imports funcionam"""
    print("=" * 60)
    print("1. TESTANDO IMPORTS")
    print("=" * 60)
    try:
        from backend.database import get_db, engine
        print("✅ database OK")
    except Exception as e:
        print(f"❌ database: {e}")
        return False
    
    try:
        from backend.models import Upload, Atestado, Client
        print("✅ models OK")
    except Exception as e:
        print(f"❌ models: {e}")
        return False
    
    try:
        from backend.excel_processor import ExcelProcessor
        print("✅ excel_processor OK")
    except Exception as e:
        print(f"❌ excel_processor: {e}")
        return False
    
    try:
        from backend.logger import log_error
        print("✅ logger OK")
    except Exception as e:
        print(f"❌ logger: {e}")
        return False
    
    try:
        from backend.main import app
        print("✅ main OK")
    except Exception as e:
        print(f"❌ main: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def testar_permissoes():
    """Testa permissões da pasta uploads"""
    print("\n" + "=" * 60)
    print("2. TESTANDO PERMISSÕES")
    print("=" * 60)
    
    uploads_dir = "/var/www/absenteismo/uploads"
    
    # Verifica se existe
    if not os.path.exists(uploads_dir):
        print(f"❌ Pasta {uploads_dir} não existe")
        try:
            os.makedirs(uploads_dir, exist_ok=True)
            print(f"✅ Pasta criada: {uploads_dir}")
        except Exception as e:
            print(f"❌ Erro ao criar pasta: {e}")
            return False
    else:
        print(f"✅ Pasta existe: {uploads_dir}")
    
    # Testa escrita
    test_file = os.path.join(uploads_dir, "test_write.txt")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
        print("✅ Permissão de escrita OK")
    except Exception as e:
        print(f"❌ Erro de permissão de escrita: {e}")
        return False
    
    return True

def testar_banco():
    """Testa conexão com banco"""
    print("\n" + "=" * 60)
    print("3. TESTANDO BANCO DE DADOS")
    print("=" * 60)
    
    try:
        from backend.database import engine
        from sqlalchemy import text
        
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("✅ Conexão com banco OK")
            
            # Verifica se tabelas existem
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='clients'"))
            if result.fetchone():
                print("✅ Tabela 'clients' existe")
            else:
                print("❌ Tabela 'clients' não existe")
                return False
            
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='uploads'"))
            if result.fetchone():
                print("✅ Tabela 'uploads' existe")
            else:
                print("❌ Tabela 'uploads' não existe")
                return False
            
            result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='atestados'"))
            if result.fetchone():
                print("✅ Tabela 'atestados' existe")
            else:
                print("❌ Tabela 'atestados' não existe")
                return False
                
    except Exception as e:
        print(f"❌ Erro no banco: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def testar_logger():
    """Testa se o logger funciona sem conflitos"""
    print("\n" + "=" * 60)
    print("4. TESTANDO LOGGER")
    print("=" * 60)
    
    try:
        from backend.logger import log_error
        
        # Testa com campos que podem causar conflito
        class TestError(Exception):
            pass
        
        try:
            log_error(
                TestError("Teste"),
                context={
                    'operation': 'test',
                    'file_name': 'test.xlsx',  # Usa file_name, não filename
                    'duration_ms': 100
                }
            )
            print("✅ Logger funciona sem conflitos")
        except KeyError as e:
            print(f"❌ Erro no logger (KeyError): {e}")
            return False
        except Exception as e:
            print(f"❌ Erro no logger: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Erro ao importar logger: {e}")
        return False
    
    return True

def main():
    """Executa todos os testes"""
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO DO SISTEMA DE UPLOAD")
    print("=" * 60 + "\n")
    
    resultados = []
    
    resultados.append(("Imports", testar_imports()))
    resultados.append(("Permissões", testar_permissoes()))
    resultados.append(("Banco de Dados", testar_banco()))
    resultados.append(("Logger", testar_logger()))
    
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    
    for nome, resultado in resultados:
        status = "✅ OK" if resultado else "❌ FALHOU"
        print(f"{nome}: {status}")
    
    todos_ok = all(r[1] for r in resultados)
    
    print("\n" + "=" * 60)
    if todos_ok:
        print("✅ TODOS OS TESTES PASSARAM!")
        print("O problema pode estar na planilha ou no processamento específico.")
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print("Corrija os problemas acima antes de tentar upload.")
    print("=" * 60 + "\n")
    
    return 0 if todos_ok else 1

if __name__ == "__main__":
    sys.exit(main())


