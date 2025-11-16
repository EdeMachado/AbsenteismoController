"""
Script para remover permanentemente o cliente fictício GrupoBiomed
"""
import sqlite3
from pathlib import Path

db_path = Path("database/absenteismo.db")

if not db_path.exists():
    print("❌ Banco de dados não encontrado!")
    exit(1)

print("=== REMOVENDO CLIENTE FICTÍCIO GRUPOBIOMED ===")

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

try:
    # Encontra o cliente GrupoBiomed
    cursor.execute("""
        SELECT id, nome, nome_fantasia FROM clients 
        WHERE nome LIKE '%GrupoBiomed%' OR nome_fantasia LIKE '%GrupoBiomed%'
    """)
    clientes = cursor.fetchall()
    
    if not clientes:
        print("✅ Cliente GrupoBiomed não encontrado no banco.")
        conn.close()
        exit(0)
    
    for cliente in clientes:
        cliente_id = cliente[0]
        nome = cliente[1]
        print(f"\n📋 Cliente encontrado: ID={cliente_id}, Nome={nome}")
        
        # Conta registros relacionados
        cursor.execute("SELECT COUNT(*) FROM uploads WHERE client_id = ?", (cliente_id,))
        total_uploads = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM atestados 
            WHERE upload_id IN (SELECT id FROM uploads WHERE client_id = ?)
        """, (cliente_id,))
        total_atestados = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM client_logos WHERE client_id = ?", (cliente_id,))
        total_logos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM client_column_mappings WHERE client_id = ?", (cliente_id,))
        total_mappings = cursor.fetchone()[0]
        
        print(f"   - Uploads: {total_uploads}")
        print(f"   - Atestados: {total_atestados}")
        print(f"   - Logos: {total_logos}")
        print(f"   - Mapeamentos: {total_mappings}")
        
        # Deleta todos os dados relacionados
        print("\n🗑️  Removendo dados relacionados...")
        
        # Deleta atestados
        cursor.execute("""
            DELETE FROM atestados 
            WHERE upload_id IN (SELECT id FROM uploads WHERE client_id = ?)
        """, (cliente_id,))
        print(f"   ✅ {cursor.rowcount} atestados removidos")
        
        # Deleta uploads
        cursor.execute("DELETE FROM uploads WHERE client_id = ?", (cliente_id,))
        print(f"   ✅ {cursor.rowcount} uploads removidos")
        
        # Deleta logos
        cursor.execute("DELETE FROM client_logos WHERE client_id = ?", (cliente_id,))
        print(f"   ✅ {cursor.rowcount} logos removidos")
        
        # Deleta mapeamentos
        cursor.execute("DELETE FROM client_column_mappings WHERE client_id = ?", (cliente_id,))
        print(f"   ✅ {cursor.rowcount} mapeamentos removidos")
        
        # Deleta filtros salvos
        cursor.execute("DELETE FROM saved_filters WHERE client_id = ?", (cliente_id,))
        print(f"   ✅ {cursor.rowcount} filtros salvos removidos")
        
        # Deleta o cliente
        cursor.execute("DELETE FROM clients WHERE id = ?", (cliente_id,))
        print(f"   ✅ Cliente removido")
        
        conn.commit()
        print(f"\n✅ Cliente GrupoBiomed (ID={cliente_id}) removido permanentemente!")
    
    print("\n🎉 Limpeza concluída com sucesso!")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro ao remover cliente: {e}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()



