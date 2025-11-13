"""Verifica mapeamento e dados do cliente 4"""
import sqlite3
import json

conn = sqlite3.connect('database/absenteismo.db')
cursor = conn.cursor()

# Verifica mapeamento
cursor.execute('SELECT column_mapping FROM client_column_mappings WHERE client_id = 4')
mapping_row = cursor.fetchone()

if mapping_row:
    try:
        mapping_data = json.loads(mapping_row[0])
        if isinstance(mapping_data, dict) and 'column_mapping' in mapping_data:
            mapping = mapping_data['column_mapping']
        else:
            mapping = mapping_data if isinstance(mapping_data, dict) else {}
        
        print('=== MAPEAMENTO DE COLUNAS ===')
        for coluna_planilha, campo_sistema in mapping.items():
            print(f'  "{coluna_planilha}" -> {campo_sistema}')
        
        # Verifica se "NOME COMPLETO" está mapeado
        nome_completo_mapeado = None
        for coluna, campo in mapping.items():
            if 'nome' in coluna.lower() and 'completo' in coluna.lower():
                nome_completo_mapeado = (coluna, campo)
                break
        
        if nome_completo_mapeado:
            print(f'\n✅ Coluna de nome encontrada: "{nome_completo_mapeado[0]}" -> {nome_completo_mapeado[1]}')
        else:
            print('\n❌ Nenhuma coluna de nome completo encontrada no mapeamento!')
    except Exception as e:
        print(f'Erro ao ler mapeamento: {e}')

# Verifica dados brutos na tabela
print('\n=== DADOS BRUTOS (primeiros 5 registros) ===')
cursor.execute('''
    SELECT id, nomecompleto, nome_funcionario, setor, dias_atestados
    FROM atestados 
    JOIN uploads ON atestados.upload_id = uploads.id 
    WHERE uploads.client_id = 4 
    LIMIT 5
''')
for row in cursor.fetchall():
    print(f'ID: {row[0]}, nomecompleto: "{row[1]}", nome_funcionario: "{row[2]}", setor: "{row[3]}", dias: {row[4]}')

conn.close()

