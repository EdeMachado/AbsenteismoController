"""
Script para limpar todos os dados do banco de dados
"""
from backend.database import get_db
from backend.models import Atestado, Upload, Client

print("=== LIMPANDO BANCO DE DADOS ===")
print("\nATENCAO: Todos os dados serao removidos!")

db = next(get_db())

try:
    # Conta registros antes
    total_atestados = db.query(Atestado).count()
    total_uploads = db.query(Upload).count()
    
    print(f"\nRegistros encontrados:")
    print(f"  - Atestados: {total_atestados}")
    print(f"  - Uploads: {total_uploads}")
    
    # Deleta todos os atestados
    print("\nRemovendo atestados...")
    db.query(Atestado).delete()
    
    # Deleta todos os uploads
    print("Removendo uploads...")
    db.query(Upload).delete()
    
    # Mantem o cliente padrao
    print("Mantendo cliente padrao...")
    
    # Commit
    db.commit()
    
    print("\nBanco de dados limpo com sucesso!")
    print("Voce pode fazer um novo upload da planilha agora.")
    
except Exception as e:
    db.rollback()
    print(f"\nErro ao limpar banco: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()

