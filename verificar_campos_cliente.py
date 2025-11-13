"""Verifica quais campos têm dados para o cliente"""
import sqlite3
import json

conn = sqlite3.connect('database/absenteismo.db')
cursor = conn.cursor()

# Verifica mapeamento do cliente 4
cursor.execute('SELECT column_mapping FROM client_column_mappings WHERE client_id = 4')
mapping_row = cursor.fetchone()

if mapping_row:
    try:
        mapping_data = json.loads(mapping_row[0])
        if isinstance(mapping_data, dict) and 'column_mapping' in mapping_data:
            mapping = mapping_data['column_mapping']
        else:
            mapping = mapping_data if isinstance(mapping_data, dict) else {}
        print('Mapeamento de colunas:')
        for coluna, campo in mapping.items():
            print(f'  {coluna} -> {campo}')
    except:
        print('Erro ao ler mapeamento')

# Verifica quais campos têm dados
campos = ['nomecompleto', 'nome_funcionario', 'setor', 'cid', 'dias_atestados', 'horas_perdi']
print('\nCampos com dados:')
for campo in campos:
    cursor.execute(f'''
        SELECT COUNT(*) 
        FROM atestados 
        JOIN uploads ON atestados.upload_id = uploads.id 
        WHERE uploads.client_id = 4 
        AND atestados.{campo} IS NOT NULL 
        AND atestados.{campo} != ""
        AND (atestados.{campo} != 0 OR atestados.{campo} IS NULL)
    ''')
    count = cursor.fetchone()[0]
    if count > 0:
        print(f'  {campo}: {count} registros')

conn.close()

