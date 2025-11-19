"""
Script para Upload em Lote de Múltiplas Planilhas
Facilita o upload de planilhas de vários meses de uma vez
"""
import sys
import os
import requests
import json
from pathlib import Path
from datetime import datetime

# Configura encoding UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def extrair_mes_referencia(nome_arquivo: str) -> str:
    """
    Tenta extrair o mês de referência do nome do arquivo
    Formatos suportados:
    - Atestados 09.2025.xlsx -> 2025-09
    - INDICADORES SETEMBRO 2025.xlsx -> 2025-09
    - 2025-09.xlsx -> 2025-09
    - setembro_2025.xlsx -> 2025-09
    """
    nome = nome_arquivo.upper()
    
    # Mapeamento de meses em português
    meses_pt = {
        'JANEIRO': '01', 'FEVEREIRO': '02', 'MARCO': '03', 'MARÇO': '03',
        'ABRIL': '04', 'MAIO': '05', 'JUNHO': '06',
        'JULHO': '07', 'AGOSTO': '08', 'SETEMBRO': '09',
        'OUTUBRO': '10', 'NOVEMBRO': '11', 'DEZEMBRO': '12',
        'JAN': '01', 'FEV': '02', 'MAR': '03', 'ABR': '04',
        'MAI': '05', 'JUN': '06', 'JUL': '07', 'AGO': '08',
        'SET': '09', 'OUT': '10', 'NOV': '11', 'DEZ': '12'
    }
    
    # Tenta formato YYYY-MM
    import re
    match = re.search(r'(\d{4})-(\d{2})', nome)
    if match:
        return f"{match.group(1)}-{match.group(2)}"
    
    # Tenta formato MM.YYYY ou MM/YYYY
    match = re.search(r'(\d{2})[./](\d{4})', nome)
    if match:
        return f"{match.group(2)}-{match.group(1)}"
    
    # Tenta encontrar mês em português
    for mes_pt, mes_num in meses_pt.items():
        if mes_pt in nome:
            # Procura ano
            ano_match = re.search(r'(\d{4})', nome)
            if ano_match:
                return f"{ano_match.group(1)}-{mes_num}"
    
    return None

def fazer_login(base_url: str, username: str, password: str) -> str:
    """Faz login e retorna o token JWT"""
    print(f"🔐 Fazendo login em {base_url}...")
    
    url = f"{base_url}/api/auth/login"
    data = {
        "username": username,
        "password": password
    }
    
    try:
        response = requests.post(url, data=data, timeout=10)
        response.raise_for_status()
        result = response.json()
        token = result.get("access_token")
        
        if token:
            print("  ✅ Login realizado com sucesso")
            return token
        else:
            print("  ❌ Token não recebido")
            return None
    except Exception as e:
        print(f"  ❌ Erro ao fazer login: {e}")
        return None

def upload_planilha(base_url: str, token: str, arquivo_path: str, client_id: int, mes_referencia: str = None) -> bool:
    """Faz upload de uma planilha"""
    nome_arquivo = os.path.basename(arquivo_path)
    
    # Se não forneceu mês, tenta extrair do nome
    if not mes_referencia:
        mes_referencia = extrair_mes_referencia(nome_arquivo)
    
    if mes_referencia:
        print(f"  📅 Mês de referência detectado: {mes_referencia}")
    else:
        print(f"  ⚠️  Não foi possível detectar o mês de referência")
        resposta = input(f"  Digite o mês de referência (YYYY-MM) ou Enter para pular: ").strip()
        if resposta:
            mes_referencia = resposta
        else:
            print(f"  ⏭️  Pulando arquivo {nome_arquivo}")
            return False
    
    print(f"  📤 Enviando {nome_arquivo}...")
    
    url = f"{base_url}/api/upload"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        with open(arquivo_path, 'rb') as f:
            files = {'file': (nome_arquivo, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            data = {
                'client_id': client_id
            }
            if mes_referencia:
                data['mes_referencia'] = mes_referencia
            
            response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
            response.raise_for_status()
            result = response.json()
            
            if result.get("success"):
                total_registros = result.get("total_registros", 0)
                print(f"  ✅ Upload concluído: {total_registros} registros processados")
                return True
            else:
                print(f"  ❌ Upload falhou: {result.get('detail', 'Erro desconhecido')}")
                return False
    except Exception as e:
        print(f"  ❌ Erro ao fazer upload: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"     Detalhes: {error_detail}")
            except:
                print(f"     Resposta: {e.response.text[:200]}")
        return False

def listar_clientes(base_url: str, token: str) -> list:
    """Lista todos os clientes disponíveis"""
    print("📋 Listando clientes...")
    
    url = f"{base_url}/api/clientes"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        clientes = response.json()
        print(f"  ✅ {len(clientes)} cliente(s) encontrado(s)")
        return clientes
    except Exception as e:
        print(f"  ❌ Erro ao listar clientes: {e}")
        return []

def main():
    """Função principal"""
    print("=" * 60)
    print("UPLOAD EM LOTE DE PLANILHAS")
    print("=" * 60)
    print()
    
    # Configurações
    base_url = input("URL do servidor (ex: http://localhost:8000 ou https://www.absenteismocontroller.com.br): ").strip()
    if not base_url:
        base_url = "http://localhost:8000"
    
    if not base_url.startswith(('http://', 'https://')):
        base_url = f"http://{base_url}"
    
    username = input("Usuário: ").strip()
    if not username:
        print("❌ Usuário é obrigatório")
        return 1
    
    password = input("Senha: ").strip()
    if not password:
        print("❌ Senha é obrigatória")
        return 1
    
    # Faz login
    token = fazer_login(base_url, username, password)
    if not token:
        print("❌ Não foi possível fazer login")
        return 1
    
    # Lista clientes
    clientes = listar_clientes(base_url, token)
    if not clientes:
        print("❌ Nenhum cliente encontrado")
        return 1
    
    print("\nClientes disponíveis:")
    for i, cliente in enumerate(clientes, 1):
        print(f"  {i}. {cliente.get('nome', 'N/A')} (ID: {cliente.get('id')})")
    
    cliente_idx = input("\nSelecione o cliente (número): ").strip()
    try:
        cliente_idx = int(cliente_idx) - 1
        cliente_selecionado = clientes[cliente_idx]
        client_id = cliente_selecionado['id']
        print(f"✅ Cliente selecionado: {cliente_selecionado.get('nome')}")
    except (ValueError, IndexError):
        print("❌ Seleção inválida")
        return 1
    
    # Seleciona pasta com planilhas
    print("\n" + "=" * 60)
    pasta = input("Caminho da pasta com as planilhas (ou Enter para usar 'Dados'): ").strip()
    if not pasta:
        pasta = "Dados"
    
    if not os.path.exists(pasta):
        print(f"❌ Pasta não encontrada: {pasta}")
        return 1
    
    # Lista arquivos Excel
    arquivos = []
    for ext in ['*.xlsx', '*.xls']:
        arquivos.extend(Path(pasta).glob(ext))
    
    if not arquivos:
        print(f"❌ Nenhum arquivo Excel encontrado em {pasta}")
        return 1
    
    print(f"\n📁 {len(arquivos)} arquivo(s) encontrado(s):")
    for i, arquivo in enumerate(arquivos, 1):
        print(f"  {i}. {arquivo.name}")
    
    confirmar = input("\nDeseja fazer upload de todos os arquivos? (s/N): ").strip().lower()
    if confirmar != 's':
        print("❌ Operação cancelada")
        return 0
    
    # Faz upload de cada arquivo
    print("\n" + "=" * 60)
    print("INICIANDO UPLOADS")
    print("=" * 60)
    
    sucessos = 0
    falhas = 0
    
    for i, arquivo in enumerate(arquivos, 1):
        print(f"\n[{i}/{len(arquivos)}] Processando: {arquivo.name}")
        if upload_planilha(base_url, token, str(arquivo), client_id):
            sucessos += 1
        else:
            falhas += 1
    
    # Resumo final
    print("\n" + "=" * 60)
    print("RESUMO")
    print("=" * 60)
    print(f"✅ Sucessos: {sucessos}")
    print(f"❌ Falhas: {falhas}")
    print(f"📊 Total: {len(arquivos)}")
    print("=" * 60)
    
    return 0 if falhas == 0 else 1

if __name__ == "__main__":
    sys.exit(main())



