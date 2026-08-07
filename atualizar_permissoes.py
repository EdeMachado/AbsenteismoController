#!/usr/bin/env python3
"""
Script para atualizar permissões de usuários
DESATIVADO (S01-A): zerava client_id de usuários existentes.
Não execute este script em produção.
"""
import sys
import os

sys.stderr.write(
    "ERRO (S01-A): atualizar_permissoes.py foi desativado. "
    "Não é permitido zerar ou reatribuir client_id em massa.\n"
)
sys.exit(2)

# Adiciona o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.database import get_db, init_db
from backend.models import User

def atualizar_permissoes():
    """Atualiza permissões de usuários"""
    init_db()
    db = next(get_db())
    
    try:
        resultado = []
        
        # Busca usuário Nilceia
        nilceia = db.query(User).filter(
            (User.username.ilike('%nilceia%')) | 
            (User.email.ilike('%nilceia%')) |
            (User.nome_completo.ilike('%nilceia%'))
        ).first()
        
        if nilceia:
            if nilceia.client_id != 2:
                nilceia.client_id = 2  # CONVERPLAST
                resultado.append(f"✅ {nilceia.username}: client_id = 2 (CONVERPLAST)")
                print(f"✅ Usuário {nilceia.username} atualizado: client_id = 2 (CONVERPLAST)")
            else:
                resultado.append(f"ℹ️ {nilceia.username}: já estava com client_id = 2")
        else:
            resultado.append("⚠️ Usuário Nilceia não encontrado")
            print("⚠️ Usuário Nilceia não encontrado")
        
        # Todos os outros usuários recebem client_id = NULL (acesso a todos)
        outros_usuarios = db.query(User).filter(
            User.id != nilceia.id if nilceia else True
        ).all()
        
        atualizados = 0
        for user in outros_usuarios:
            if user.client_id is not None:
                user.client_id = None
                atualizados += 1
                resultado.append(f"✅ {user.username}: client_id = NULL (acesso a todos)")
                print(f"✅ Usuário {user.username} atualizado: client_id = NULL (acesso a todos)")
        
        db.commit()
        
        print("\n" + "="*60)
        print("RESUMO DA ATUALIZAÇÃO DE PERMISSÕES")
        print("="*60)
        for item in resultado:
            print(item)
        print("="*60)
        print(f"\n✅ Total: {atualizados + (1 if nilceia and nilceia.client_id == 2 else 0)} usuários atualizados")
        print("✅ Nilceia: acesso apenas a CONVERPLAST (client_id = 2)")
        print("✅ Demais usuários: acesso a todos os clientes (client_id = NULL)")
        print("="*60)
        
        return True
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"\n❌ Erro ao atualizar permissões: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔄 Atualizando permissões de usuários...\n")
    sucesso = atualizar_permissoes()
    sys.exit(0 if sucesso else 1)

