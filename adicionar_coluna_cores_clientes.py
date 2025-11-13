import sqlite3
import os
import json

db_path = os.path.join(os.path.dirname(__file__), 'database', 'absenteismo.db')

def adicionar_coluna_cores():
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se a coluna já existe
        cursor.execute("PRAGMA table_info(clients)")
        colunas_existentes = [col[1] for col in cursor.fetchall()]
        
        if 'cores_personalizadas' not in colunas_existentes:
            print("Adicionando coluna 'cores_personalizadas'...")
            cursor.execute("ALTER TABLE clients ADD COLUMN cores_personalizadas TEXT")
            print("✓ Coluna 'cores_personalizadas' adicionada com sucesso!")
        else:
            print("✓ Coluna 'cores_personalizadas' já existe")
        
        # Configura cores padrão para Converplast (se existir)
        cursor.execute("SELECT id, nome FROM clients WHERE nome LIKE '%CONVERPLAST%' OR nome LIKE '%Converplast%'")
        converplast = cursor.fetchone()
        if converplast:
            cores_converplast = {
                "primary": "#1a237e",
                "primaryDark": "#0d47a1",
                "primaryLight": "#3949ab",
                "primaryLighter": "#5c6bc0",
                "secondary": "#556B2F",
                "secondaryDark": "#4a5d23",
                "secondaryLight": "#6B8E23",
                "secondaryLighter": "#808000",
                "paleta": ["#1a237e", "#556B2F", "#0d47a1", "#6B8E23", "#3949ab", "#808000", "#5c6bc0", "#4a5d23"]
            }
            cursor.execute(
                "UPDATE clients SET cores_personalizadas = ? WHERE id = ?",
                (json.dumps(cores_converplast), converplast[0])
            )
            print(f"✓ Cores padrão configuradas para {converplast[1]}")
        
        # Configura cores padrão para Roda de Ouro (se existir)
        cursor.execute("SELECT id, nome FROM clients WHERE nome LIKE '%RODA%OURO%' OR nome LIKE '%Roda%Ouro%'")
        roda_ouro = cursor.fetchone()
        if roda_ouro:
            cores_roda_ouro = {
                "primary": "#000000",
                "primaryDark": "#1a1a1a",
                "primaryLight": "#333333",
                "primaryLighter": "#4d4d4d",
                "secondary": "#D4AF37",
                "secondaryDark": "#B8941F",
                "secondaryLight": "#E5C158",
                "secondaryLighter": "#F5D896",
                "paleta": ["#000000", "#D4AF37", "#1a1a1a", "#E5C158", "#333333", "#F5D896", "#4d4d4d", "#B8941F"]
            }
            cursor.execute(
                "UPDATE clients SET cores_personalizadas = ? WHERE id = ?",
                (json.dumps(cores_roda_ouro), roda_ouro[0])
            )
            print(f"✓ Cores padrão configuradas para {roda_ouro[1]}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migração concluída com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar coluna: {e}")
        if conn:
            conn.rollback()
            conn.close()
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        if conn:
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Migração: Adicionando coluna de cores personalizadas")
    print("=" * 60)
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
    else:
        print(f"📁 Banco de dados: {db_path}")
        print()
        adicionar_coluna_cores()
        print()
        print("=" * 60)

