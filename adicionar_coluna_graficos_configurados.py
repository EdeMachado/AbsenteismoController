"""
Script para adicionar coluna graficos_configurados na tabela client_column_mappings
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join('database', 'absenteismo.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verifica se a coluna já existe
    cursor.execute("PRAGMA table_info(client_column_mappings)")
    colunas = cursor.fetchall()
    colunas_existentes = [col[1] for col in colunas]
    
    if 'graficos_configurados' not in colunas_existentes:
        print("Adicionando coluna graficos_configurados...")
        cursor.execute("""
            ALTER TABLE client_column_mappings 
            ADD COLUMN graficos_configurados TEXT
        """)
        conn.commit()
        print("✅ Coluna graficos_configurados adicionada com sucesso!")
    else:
        print("ℹ️ Coluna graficos_configurados já existe.")
    
    conn.close()
    print("✅ Migração concluída!")
    
except Exception as e:
    print(f"❌ Erro na migração: {e}")
    if conn:
        conn.close()

