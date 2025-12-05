# 🚀 Deploy - Exclusão de Usuários + Limitação por Empresa

## 📋 O que foi implementado:

1. ✅ Botão de **excluir usuário** no módulo Configurações
2. ✅ Campo para **limitar acesso por empresa** ao cadastrar/editar usuário
3. ✅ Migração automática do banco de dados (adiciona coluna `client_id`)

---

## 🔄 PASSO 1: Commit e Push (Local)

**Execute no PowerShell (na pasta do projeto):**

```powershell
# Verificar alterações
git status

# Adicionar arquivos modificados
git add backend/models.py
git add backend/main.py
git add backend/database.py
git add frontend/configuracoes.html
git add frontend/static/js/configuracoes.js

# Fazer commit
git commit -m "Adicionar exclusão de usuários e limitação de acesso por empresa

- Adicionado botão de excluir usuário no módulo Configurações
- Adicionado campo client_id no modelo User para limitar acesso por empresa
- Adicionada rota DELETE /api/users/{user_id}
- Atualizadas rotas POST e PUT para incluir client_id
- Adicionada migração automática para coluna client_id
- Atualizado frontend com seleção de empresa nos modais de usuário"

# Fazer push
git push origin main
```

---

## 🔐 PASSO 2: Deploy no Servidor (SSH)

**Conecte-se ao servidor Hostinger:**

```bash
ssh -p 65002 SEU_USUARIO@72.60.166.55
```

**Depois de conectar, execute:**

```bash
# Navegar para o diretório do sistema
cd ~/domains/absenteismocontroller.com.br/public_html/absenteismo

# OU se o caminho for diferente:
# cd ~/public_html/absenteismo

# Fazer pull das alterações
git pull origin main

# A migração será executada automaticamente na próxima inicialização
# Mas podemos executar manualmente para garantir:
source venv/bin/activate
python3 -c "from backend.database import run_migrations; run_migrations(); print('Migração concluída!')"

# Reiniciar o servidor (se estiver usando systemd/supervisor)
# OU apenas reinicie o gunicorn se estiver rodando manualmente
```

---

## ✅ PASSO 3: Verificar Deploy

1. Acesse: https://www.absenteismocontroller.com.br
2. Faça login como administrador
3. Vá em **Configurações**
4. Verifique:
   - ✅ Botão de excluir (ícone de lixeira) ao lado de cada usuário
   - ✅ Campo "Empresa (Acesso Limitado)" no modal de novo usuário
   - ✅ Campo "Empresa (Acesso Limitado)" no modal de editar usuário
   - ✅ Coluna "Empresa" na tabela de usuários

---

## 🧪 Testar Funcionalidades

### Teste 1: Excluir Usuário
1. Vá em Configurações → Gestão de Usuários
2. Clique no botão de lixeira (🗑️) ao lado de um usuário
3. Confirme a exclusão
4. Verifique se o usuário foi removido da lista

### Teste 2: Limitar Acesso por Empresa
1. Clique em "Novo Usuário"
2. Preencha os dados
3. **Selecione uma empresa** no campo "Empresa (Acesso Limitado)"
4. Crie o usuário
5. Verifique se a empresa aparece na tabela

---

## 🆘 Troubleshooting

### Erro: "Column client_id does not exist"
**Solução:** Execute a migração manualmente:
```bash
python3 -c "from backend.database import run_migrations; run_migrations()"
```

### Erro: "Cannot delete own user"
**Isso é normal!** O sistema protege para que você não exclua seu próprio usuário.

### Erro: "Company not found"
**Solução:** Verifique se a empresa existe no sistema antes de associar ao usuário.

---

## 📝 Notas Importantes

- ⚠️ A migração adiciona a coluna `client_id` automaticamente
- ⚠️ Usuários existentes terão `client_id = NULL` (acesso a todas as empresas)
- ⚠️ A limitação de acesso por empresa ainda precisa ser implementada na lógica de filtros (próxima etapa)

---

**Pronto para deploy! 🚀**

