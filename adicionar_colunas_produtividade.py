"""
Script para adicionar as colunas sinistralidade e pericia_indireta à tabela produtividade
"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'database', 'absenteismo.db')

def adicionar_colunas():
    """Adiciona as novas colunas à tabela produtividade"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verifica se as colunas já existem
        cursor.execute("PRAGMA table_info(produtividade)")
        colunas_existentes = [col[1] for col in cursor.fetchall()]
        
        # Adiciona sinistralidade se não existir
        if 'sinistralidade' not in colunas_existentes:
            print("Adicionando coluna 'sinistralidade'...")
            cursor.execute("ALTER TABLE produtividade ADD COLUMN sinistralidade INTEGER DEFAULT 0")
            print("✓ Coluna 'sinistralidade' adicionada com sucesso!")
        else:
            print("✓ Coluna 'sinistralidade' já existe")
        
        # Adiciona pericia_indireta se não existir
        if 'pericia_indireta' not in colunas_existentes:
            print("Adicionando coluna 'pericia_indireta'...")
            cursor.execute("ALTER TABLE produtividade ADD COLUMN pericia_indireta INTEGER DEFAULT 0")
            print("✓ Coluna 'pericia_indireta' adicionada com sucesso!")
        else:
            print("✓ Coluna 'pericia_indireta' já existe")
        
        # Atualiza o total para incluir as novas colunas
        print("\nAtualizando valores de 'total' para incluir as novas colunas...")
        cursor.execute("""
            UPDATE produtividade 
            SET total = (
                COALESCE(ocupacionais, 0) +
                COALESCE(assistenciais, 0) +
                COALESCE(acidente_trabalho, 0) +
                COALESCE(inss, 0) +
                COALESCE(sinistralidade, 0) +
                COALESCE(absenteismo, 0) +
                COALESCE(pericia_indireta, 0)
            )
        """)
        
        linhas_afetadas = cursor.rowcount
        print(f"✓ {linhas_afetadas} registro(s) atualizado(s)")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Migração concluída com sucesso!")
        
    except sqlite3.Error as e:
        print(f"❌ Erro ao adicionar colunas: {e}")
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
    print("Migração: Adicionando colunas à tabela produtividade")
    print("=" * 60)
    print()
    
    if not os.path.exists(db_path):
        print(f"❌ Banco de dados não encontrado em: {db_path}")
    else:
        print(f"📁 Banco de dados: {db_path}")
        print()
        adicionar_colunas()
        print()
        print("=" * 60)


