"""Verifica dados salvos após upload da Roda de Ouro"""
import sqlite3
import json

conn = sqlite3.connect('database/absenteismo.db')
cursor = conn.cursor()

# Verifica uploads recentes do cliente 4
cursor.execute('''
    SELECT id, filename, uploaded_at, client_id 
    FROM uploads 
    WHERE client_id = 4 
    ORDER BY uploaded_at DESC 
    LIMIT 5
''')
uploads = cursor.fetchall()

print('=== UPLOADS DO CLIENTE 4 ===')
if uploads:
    for upload in uploads:
        print(f'  ID: {upload[0]}, Arquivo: {upload[1]}, Data: {upload[2]}')
else:
    print('  ❌ Nenhum upload encontrado!')
    conn.close()
    exit(1)

# Verifica mapeamento
cursor.execute('SELECT column_mapping FROM client_column_mappings WHERE client_id = 4')
mapping_row = cursor.fetchone()

print('\n=== MAPEAMENTO ===')
if mapping_row:
    try:
        mapping_data = json.loads(mapping_row[0])
        if isinstance(mapping_data, dict) and 'column_mapping' in mapping_data:
            mapping = mapping_data['column_mapping']
        else:
            mapping = mapping_data if isinstance(mapping_data, dict) else {}
        
        for coluna_planilha, campo_sistema in mapping.items():
            print(f'  "{coluna_planilha}" -> {campo_sistema}')
    except Exception as e:
        print(f'  Erro ao ler mapeamento: {e}')
else:
    print('  ❌ Nenhum mapeamento encontrado!')

# Verifica dados salvos
print('\n=== DADOS SALVOS (primeiros 10 registros) ===')
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
    ORDER BY atestados.id DESC
    LIMIT 10
''')
rows = cursor.fetchall()

if rows:
    print(f'Total de registros: {len(rows)}')
    for row in rows:
        nome = row[1] if row[1] else '(vazio)'
        setor = row[3] if row[3] else '(vazio)'
        dias = row[4] if row[4] else 0
        print(f'  ID: {row[0]}, nomecompleto: "{nome}", setor: "{setor}", dias: {dias}, arquivo: {row[5]}')
    
    # Conta registros com nomecompleto
    cursor.execute('''
        SELECT COUNT(*) 
        FROM atestados 
        JOIN uploads ON atestados.upload_id = uploads.id 
        WHERE uploads.client_id = 4 
        AND atestados.nomecompleto IS NOT NULL 
        AND atestados.nomecompleto != ''
    ''')
    count_nome = cursor.fetchone()[0]
    print(f'\n✅ Registros com nomecompleto preenchido: {count_nome}')
    
    # Conta registros com setor
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
else:
    print('  ❌ Nenhum registro encontrado!')

conn.close()

