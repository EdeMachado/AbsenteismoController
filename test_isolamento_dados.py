"""
Script de Teste de Isolamento de Dados entre Empresas
Verifica se os dados de diferentes clientes estão isolados corretamente
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

from sqlalchemy.orm import Session
from backend.database import get_db, init_db
from backend.models import Client, Upload, Atestado
from backend.auth import get_password_hash
from backend.validators import validate_client_data_integrity
from datetime import datetime
import json

def criar_clientes_teste(db: Session):
    """Cria clientes de teste para validar isolamento"""
    print("📋 Criando clientes de teste...")
    
    # Cliente 1
    cliente1 = db.query(Client).filter(Client.nome == "TESTE_ISOLAMENTO_1").first()
    if not cliente1:
        cliente1 = Client(
            nome="TESTE_ISOLAMENTO_1",
            nome_fantasia="Teste Isolamento 1",
            cnpj="00.000.000/0001-01"
        )
        db.add(cliente1)
        db.commit()
        db.refresh(cliente1)
        print(f"  ✅ Cliente 1 criado (ID: {cliente1.id})")
    else:
        print(f"  ℹ️  Cliente 1 já existe (ID: {cliente1.id})")
    
    # Cliente 2
    cliente2 = db.query(Client).filter(Client.nome == "TESTE_ISOLAMENTO_2").first()
    if not cliente2:
        cliente2 = Client(
            nome="TESTE_ISOLAMENTO_2",
            nome_fantasia="Teste Isolamento 2",
            cnpj="00.000.000/0001-02"
        )
        db.add(cliente2)
        db.commit()
        db.refresh(cliente2)
        print(f"  ✅ Cliente 2 criado (ID: {cliente2.id})")
    else:
        print(f"  ℹ️  Cliente 2 já existe (ID: {cliente2.id})")
    
    return cliente1, cliente2

def criar_dados_teste(db: Session, cliente1: Client, cliente2: Client):
    """Cria dados de teste para cada cliente"""
    print("\n📊 Criando dados de teste...")
    
    # Upload para Cliente 1
    upload1 = db.query(Upload).filter(
        Upload.client_id == cliente1.id,
        Upload.mes_referencia == "2025-01"
    ).first()
    
    if not upload1:
        upload1 = Upload(
            client_id=cliente1.id,
            filename="teste_cliente1.xlsx",
            mes_referencia="2025-01",
            total_registros=2
        )
        db.add(upload1)
        db.commit()
        db.refresh(upload1)
        print(f"  ✅ Upload Cliente 1 criado (ID: {upload1.id})")
    else:
        print(f"  ℹ️  Upload Cliente 1 já existe (ID: {upload1.id})")
    
    # Atestados para Cliente 1
    atestado1_1 = db.query(Atestado).filter(
        Atestado.upload_id == upload1.id,
        Atestado.nomecompleto == "FUNCIONARIO_CLIENTE_1"
    ).first()
    
    if not atestado1_1:
        atestado1_1 = Atestado(
            upload_id=upload1.id,
            nomecompleto="FUNCIONARIO_CLIENTE_1",
            dias_atestados=5.0,
            horas_perdi=40.0,
            cid="Z00.0",
            diagnostico="Teste Cliente 1",
            setor="SETOR_CLIENTE_1"
        )
        db.add(atestado1_1)
        print(f"  ✅ Atestado 1 Cliente 1 criado")
    
    # Upload para Cliente 2
    upload2 = db.query(Upload).filter(
        Upload.client_id == cliente2.id,
        Upload.mes_referencia == "2025-01"
    ).first()
    
    if not upload2:
        upload2 = Upload(
            client_id=cliente2.id,
            filename="teste_cliente2.xlsx",
            mes_referencia="2025-01",
            total_registros=2
        )
        db.add(upload2)
        db.commit()
        db.refresh(upload2)
        print(f"  ✅ Upload Cliente 2 criado (ID: {upload2.id})")
    else:
        print(f"  ℹ️  Upload Cliente 2 já existe (ID: {upload2.id})")
    
    # Atestados para Cliente 2
    atestado2_1 = db.query(Atestado).filter(
        Atestado.upload_id == upload2.id,
        Atestado.nomecompleto == "FUNCIONARIO_CLIENTE_2"
    ).first()
    
    if not atestado2_1:
        atestado2_1 = Atestado(
            upload_id=upload2.id,
            nomecompleto="FUNCIONARIO_CLIENTE_2",
            dias_atestados=10.0,
            horas_perdi=80.0,
            cid="Z00.1",
            diagnostico="Teste Cliente 2",
            setor="SETOR_CLIENTE_2"
        )
        db.add(atestado2_1)
        print(f"  ✅ Atestado 1 Cliente 2 criado")
    
    db.commit()
    return upload1, upload2

def testar_isolamento(db: Session, cliente1: Client, cliente2: Client):
    """Testa se os dados estão isolados corretamente"""
    print("\n🔒 Testando isolamento de dados...")
    
    erros = []
    
    # Teste 1: Cliente 1 não deve ver dados do Cliente 2
    print("\n  Teste 1: Cliente 1 não deve ver dados do Cliente 2")
    atestados_cliente1 = db.query(Atestado).join(Upload).filter(
        Upload.client_id == cliente1.id
    ).all()
    
    for atestado in atestados_cliente1:
        if "CLIENTE_2" in (atestado.nomecompleto or ""):
            erros.append(f"❌ Cliente 1 vê dados do Cliente 2: {atestado.nomecompleto}")
        if "CLIENTE_2" in (atestado.setor or ""):
            erros.append(f"❌ Cliente 1 vê setor do Cliente 2: {atestado.setor}")
    
    if not erros:
        print("    ✅ Passou: Cliente 1 não vê dados do Cliente 2")
    
    # Teste 2: Cliente 2 não deve ver dados do Cliente 1
    print("\n  Teste 2: Cliente 2 não deve ver dados do Cliente 1")
    atestados_cliente2 = db.query(Atestado).join(Upload).filter(
        Upload.client_id == cliente2.id
    ).all()
    
    for atestado in atestados_cliente2:
        if "CLIENTE_1" in (atestado.nomecompleto or ""):
            erros.append(f"❌ Cliente 2 vê dados do Cliente 1: {atestado.nomecompleto}")
        if "CLIENTE_1" in (atestado.setor or ""):
            erros.append(f"❌ Cliente 2 vê setor do Cliente 1: {atestado.setor}")
    
    if not erros:
        print("    ✅ Passou: Cliente 2 não vê dados do Cliente 1")
    
    # Teste 3: Contagem de registros
    print("\n  Teste 3: Contagem de registros por cliente")
    count_cliente1 = db.query(Atestado).join(Upload).filter(
        Upload.client_id == cliente1.id
    ).count()
    
    count_cliente2 = db.query(Atestado).join(Upload).filter(
        Upload.client_id == cliente2.id
    ).count()
    
    print(f"    Cliente 1: {count_cliente1} atestados")
    print(f"    Cliente 2: {count_cliente2} atestados")
    
    if count_cliente1 > 0 and count_cliente2 > 0:
        print("    ✅ Passou: Ambos os clientes têm dados isolados")
    else:
        erros.append(f"❌ Contagem incorreta: Cliente 1={count_cliente1}, Cliente 2={count_cliente2}")
    
    # Teste 4: Validação de integridade
    print("\n  Teste 4: Validação de integridade dos dados")
    try:
        resultado1 = validate_client_data_integrity(db, cliente1.id)
        resultado2 = validate_client_data_integrity(db, cliente2.id)
        
        if resultado1['valid'] and resultado2['valid']:
            print("    ✅ Passou: Integridade dos dados validada")
        else:
            erros.append(f"❌ Problemas de integridade detectados")
            print(f"    Cliente 1 issues: {resultado1.get('issues', [])}")
            print(f"    Cliente 2 issues: {resultado2.get('issues', [])}")
    except Exception as e:
        erros.append(f"❌ Erro na validação de integridade: {e}")
    
    return erros

def limpar_dados_teste(db: Session, cliente1: Client, cliente2: Client):
    """Remove dados de teste"""
    print("\n🧹 Limpando dados de teste...")
    
    # Remove atestados
    uploads1 = db.query(Upload).filter(Upload.client_id == cliente1.id).all()
    for upload in uploads1:
        db.query(Atestado).filter(Atestado.upload_id == upload.id).delete()
        db.delete(upload)
    
    uploads2 = db.query(Upload).filter(Upload.client_id == cliente2.id).all()
    for upload in uploads2:
        db.query(Atestado).filter(Atestado.upload_id == upload.id).delete()
        db.delete(upload)
    
    # Remove clientes
    db.delete(cliente1)
    db.delete(cliente2)
    
    db.commit()
    print("  ✅ Dados de teste removidos")

def main():
    """Função principal"""
    print("=" * 60)
    print("TESTE DE ISOLAMENTO DE DADOS ENTRE EMPRESAS")
    print("=" * 60)
    
    # Inicializa banco
    init_db()
    
    # Obtém sessão do banco
    db = next(get_db())
    
    try:
        # Cria clientes de teste
        cliente1, cliente2 = criar_clientes_teste(db)
        
        # Cria dados de teste
        upload1, upload2 = criar_dados_teste(db, cliente1, cliente2)
        
        # Testa isolamento
        erros = testar_isolamento(db, cliente1, cliente2)
        
        # Resultado final
        print("\n" + "=" * 60)
        if erros:
            print("❌ TESTE FALHOU")
            print(f"   {len(erros)} erro(s) encontrado(s):")
            for erro in erros:
                print(f"   {erro}")
            return 1
        else:
            print("✅ TESTE PASSOU - Isolamento de dados garantido!")
            print("=" * 60)
            return 0
    
    except Exception as e:
        print(f"\n❌ ERRO: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        # Pergunta se deve limpar dados de teste
        resposta = input("\nDeseja remover os dados de teste? (s/N): ").strip().lower()
        if resposta == 's':
            try:
                limpar_dados_teste(db, cliente1, cliente2)
            except:
                pass
        db.close()

if __name__ == "__main__":
    sys.exit(main())

