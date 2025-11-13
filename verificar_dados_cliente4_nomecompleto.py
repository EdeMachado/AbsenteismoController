"""Verifica se nomecompleto está sendo salvo corretamente para cliente 4"""
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
        
        print('=== MAPEAMENTO ===')
        for coluna_planilha, campo_sistema in mapping.items():
            print(f'  "{coluna_planilha}" -> {campo_sistema}')
        
        # Verifica qual coluna está mapeada para nomecompleto
        coluna_nome = None
        for col, campo in mapping.items():
            if campo == 'nomecompleto':
                coluna_nome = col
                break
        
        print(f'\n📋 Coluna mapeada para nomecompleto: "{coluna_nome}"')
    except Exception as e:
        print(f'Erro ao ler mapeamento: {e}')

# Verifica dados na tabela atestados
print('\n=== DADOS NA TABELA ATESTADOS (cliente 4) ===')
cursor.execute('''
    SELECT 
        atestados.id,
        atestados.nomecompleto,
        atestados.nome_funcionario,
        atestados.setor,
        atestados.dias_atestados,
        uploads.filename
    FROM atestados 
    JOIN uploads ON atestados.upload_id = uploads.id 
    WHERE uploads.client_id = 4 
    LIMIT 10
''')
rows = cursor.fetchall()
print(f'Total de registros encontrados: {len(rows)}')

if rows:
    print('\nPrimeiros 10 registros:')
    for row in rows:
        print(f'  ID: {row[0]}, nomecompleto: "{row[1]}", nome_funcionario: "{row[2]}", setor: "{row[3]}", dias: {row[4]}, arquivo: {row[5]}')
    
    # Conta quantos têm nomecompleto preenchido
    cursor.execute('''
        SELECT COUNT(*) 
        FROM atestados 
        JOIN uploads ON atestados.upload_id = uploads.id 
        WHERE uploads.client_id = 4 
        AND atestados.nomecompleto IS NOT NULL 
        AND atestados.nomecompleto != ''
    ''')
    count_nomecompleto = cursor.fetchone()[0]
    print(f'\n✅ Registros com nomecompleto preenchido: {count_nomecompleto}')
    
    # Conta quantos têm setor preenchido
    cursor.execute('''
        SELECT COUNT(*) 
        FROM atestados 
        JOIN uploads ON atestados.upload_id = uploads.id 
        WHERE uploads.client_id = 4 
        AND atestados.setor IS NOT NULL 
        AND atestados.setor != ''
    ''')
    count_setor = cursor.fetchone()[0]
    print(f'✅ Registros com setor preenchido: {count_setor}')
    
    # Conta quantos têm dias_atestados
    cursor.execute('''
        SELECT COUNT(*) 
        FROM atestados 
        JOIN uploads ON atestados.upload_id = uploads.id 
        WHERE uploads.client_id = 4 
        AND atestados.dias_atestados IS NOT NULL 
        AND atestados.dias_atestados > 0
    ''')
    count_dias = cursor.fetchone()[0]
    print(f'✅ Registros com dias_atestados > 0: {count_dias}')
else:
    print('❌ Nenhum registro encontrado para cliente 4!')

conn.close()

