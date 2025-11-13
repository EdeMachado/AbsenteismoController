"""Verifica dados do cliente no banco"""
import sqlite3

conn = sqlite3.connect('database/absenteismo.db')
cursor = conn.cursor()

# Verifica registros para cliente 4
cursor.execute('''
    SELECT COUNT(*) 
    FROM atestados 
    JOIN uploads ON atestados.upload_id = uploads.id 
    WHERE uploads.client_id = 4
''')
total = cursor.fetchone()[0]
print(f'Total de registros para cliente 4: {total}')

cursor.execute('''
    SELECT COUNT(*) 
    FROM atestados 
    JOIN uploads ON atestados.upload_id = uploads.id 
    WHERE uploads.client_id = 4 
    AND atestados.nomecompleto IS NOT NULL 
    AND atestados.nomecompleto != ""
''')
com_nome = cursor.fetchone()[0]
print(f'Registros com nomecompleto: {com_nome}')

cursor.execute('''
    SELECT COUNT(*) 
    FROM atestados 
    JOIN uploads ON atestados.upload_id = uploads.id 
    WHERE uploads.client_id = 4 
    AND atestados.dias_atestados IS NOT NULL
''')
com_dias = cursor.fetchone()[0]
print(f'Registros com dias_atestados: {com_dias}')

# Mostra uma amostra
cursor.execute('''
    SELECT atestados.nomecompleto, atestados.dias_atestados
    FROM atestados 
    JOIN uploads ON atestados.upload_id = uploads.id 
    WHERE uploads.client_id = 4 
    AND atestados.nomecompleto IS NOT NULL 
    AND atestados.nomecompleto != ""
    LIMIT 5
''')
amostra = cursor.fetchall()
print(f'\nAmostra de dados:')
for row in amostra:
    print(f'  {row[0]}: {row[1]} dias')

conn.close()

