"""
Script de Configuração para Produção
Ajusta configurações do sistema para ambiente de produção
"""
import os
import sys
import re

def atualizar_cors():
    """Atualiza configuração de CORS para produção"""
    arquivo = "backend/main.py"
    
    print(f"📝 Atualizando CORS em {arquivo}...")
    
    with open(arquivo, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    # Procura configuração de CORS
    padrao = r"allow_origins=\[.*?\]"
    
    novo_cors = '''allow_origins=[
        "https://www.absenteismocontroller.com.br",
        "https://absenteismocontroller.com.br"
    ]'''
    
    if re.search(padrao, conteudo):
        conteudo = re.sub(padrao, novo_cors, conteudo, flags=re.DOTALL)
        print("  ✅ CORS atualizado para domínios de produção")
    else:
        print("  ⚠️  Configuração de CORS não encontrada")
    
    with open(arquivo, 'w', encoding='utf-8') as f:
        f.write(conteudo)

def verificar_env():
    """Verifica se arquivo .env está configurado"""
    print("\n🔐 Verificando arquivo .env...")
    
    if not os.path.exists('.env'):
        print("  ⚠️  Arquivo .env não encontrado")
        print("     Crie um arquivo .env com SECRET_KEY")
        return False
    
    with open('.env', 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    if 'SECRET_KEY=' not in conteudo or 'SECRET_KEY=your-secret-key' in conteudo:
        print("  ⚠️  SECRET_KEY não configurada ou usando valor padrão")
        return False
    
    if 'ENVIRONMENT=production' not in conteudo:
        print("  ⚠️  ENVIRONMENT não está definido como 'production'")
        print("     Adicione: ENVIRONMENT=production")
    
    print("  ✅ Arquivo .env encontrado")
    return True

def main():
    """Função principal"""
    print("=" * 60)
    print("CONFIGURAÇÃO PARA PRODUÇÃO")
    print("=" * 60)
    
    # Verifica se está em modo produção
    ambiente = os.getenv('ENVIRONMENT', 'development')
    if ambiente != 'production':
        resposta = input("\n⚠️  ENVIRONMENT não está definido como 'production'. Continuar? (s/N): ")
        if resposta.lower() != 's':
            print("❌ Operação cancelada")
            return 1
    
    # Atualiza CORS
    atualizar_cors()
    
    # Verifica .env
    verificar_env()
    
    print("\n" + "=" * 60)
    print("✅ Configuração concluída!")
    print("=" * 60)
    print("\nPróximos passos:")
    print("1. Verifique o arquivo .env")
    print("2. Revise as configurações de CORS")
    print("3. Execute os testes: python validar_seguranca.py")
    print("4. Siga o GUIA_DEPLOY_PRODUCAO.md para deploy")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())



