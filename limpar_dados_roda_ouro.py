"""Remove todos os dados da empresa Roda de Ouro (cliente 4)"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database/absenteismo.db')
cursor = conn.cursor()

# Identifica o cliente Roda de Ouro
cursor.execute('SELECT id, nome FROM clients WHERE id = 4 OR nome LIKE "%RODA%OURO%" OR nome LIKE "%Roda%Ouro%"')
cliente = cursor.fetchone()

if not cliente:
    print("❌ Cliente Roda de Ouro não encontrado!")
    conn.close()
    exit(1)

client_id = cliente[0]
client_name = cliente[1]

print(f"🗑️ Removendo todos os dados do cliente: {client_name} (ID: {client_id})")
print("⚠️ ATENÇÃO: Esta operação não pode ser desfeita!\n")

# Conta registros antes de deletar
cursor.execute('SELECT COUNT(*) FROM uploads WHERE client_id = ?', (client_id,))
total_uploads = cursor.fetchone()[0]

cursor.execute('''
    SELECT COUNT(*) FROM atestados 
    JOIN uploads ON atestados.upload_id = uploads.id 
    WHERE uploads.client_id = ?
''', (client_id,))
total_atestados = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM produtividade WHERE client_id = ?', (client_id,))
total_produtividade = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM client_column_mappings WHERE client_id = ?', (client_id,))
total_mappings = cursor.fetchone()[0]

print(f"📊 Dados encontrados:")
print(f"   - Uploads: {total_uploads}")
print(f"   - Atestados: {total_atestados}")
print(f"   - Produtividade: {total_produtividade}")
print(f"   - Mapeamentos: {total_mappings}")

print("\n🗑️ Iniciando remoção automática...")

try:
    # 1. Deleta atestados relacionados
    cursor.execute('''
        DELETE FROM atestados 
        WHERE upload_id IN (SELECT id FROM uploads WHERE client_id = ?)
    ''', (client_id,))
    atestados_deletados = cursor.rowcount
    print(f"   ✅ {atestados_deletados} atestados deletados")
    
    # 2. Deleta uploads
    cursor.execute('DELETE FROM uploads WHERE client_id = ?', (client_id,))
    uploads_deletados = cursor.rowcount
    print(f"   ✅ {uploads_deletados} uploads deletados")
    
    # 3. Deleta produtividade
    cursor.execute('DELETE FROM produtividade WHERE client_id = ?', (client_id,))
    produtividade_deletada = cursor.rowcount
    print(f"   ✅ {produtividade_deletada} registros de produtividade deletados")
    
    # 4. Deleta mapeamentos de colunas
    cursor.execute('DELETE FROM client_column_mappings WHERE client_id = ?', (client_id,))
    mappings_deletados = cursor.rowcount
    print(f"   ✅ {mappings_deletados} mapeamentos deletados")
    
    # 5. Deleta alertas relacionados (se a tabela existir)
    try:
        cursor.execute('DELETE FROM alertas WHERE client_id = ?', (client_id,))
        alertas_deletados = cursor.rowcount
        if alertas_deletados > 0:
            print(f"   ✅ {alertas_deletados} alertas deletados")
    except sqlite3.OperationalError:
        pass  # Tabela não existe, ignora
    
    # 6. Deleta insights relacionados (se a tabela existir)
    try:
        cursor.execute('DELETE FROM insights WHERE client_id = ?', (client_id,))
        insights_deletados = cursor.rowcount
        if insights_deletados > 0:
            print(f"   ✅ {insights_deletados} insights deletados")
    except sqlite3.OperationalError:
        pass  # Tabela não existe, ignora
    
    # Commit das alterações
    conn.commit()
    
    print(f"\n✅ Todos os dados do cliente '{client_name}' foram removidos com sucesso!")
    print(f"   - Converplast (cliente 2) permanece intacta")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ Erro ao deletar dados: {e}")
    raise

finally:
    conn.close()

