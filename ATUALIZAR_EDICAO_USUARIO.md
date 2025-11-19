# 🔄 ATUALIZAR FUNCIONALIDADE DE EDIÇÃO DE USUÁRIO

## Arquivos Modificados

1. `backend/main.py` - Adicionada rota `PUT /api/users/{user_id}`
2. `frontend/configuracoes.html` - Adicionado modal de edição
3. `frontend/static/js/configuracoes.js` - Implementada função de edição

## Como Atualizar no Servidor

### PASSO 1: Enviar arquivos atualizados

No terminal local (PowerShell), execute:

```powershell
# Conectar via SCP e enviar arquivos
scp backend/main.py root@72.60.166.55:/var/www/absenteismo/backend/
scp frontend/configuracoes.html root@72.60.166.55:/var/www/absenteismo/frontend/
scp frontend/static/js/configuracoes.js root@72.60.166.55:/var/www/absenteismo/frontend/static/js/
```

### PASSO 2: No servidor (Hostinger)

```bash
# Entrar no diretório
cd /var/www/absenteismo

# Ativar ambiente virtual
source venv/bin/activate

# Reiniciar serviço
systemctl restart absenteismo

# Verificar se está rodando
systemctl status absenteismo
```

### PASSO 3: Testar

1. Acesse: https://www.absenteismocontroller.com.br/configuracoes
2. Clique no botão de editar (ícone de lápis) em um usuário
3. Edite os campos desejados
4. Clique em "Salvar"

## Funcionalidades Implementadas

✅ Editar username
✅ Editar email
✅ Alterar senha (opcional - deixe em branco para não alterar)
✅ Editar nome completo
✅ Alterar status de administrador
✅ Ativar/desativar usuário

## Proteções de Segurança

- Apenas administradores podem editar usuários
- Não é possível editar seu próprio usuário (proteção)
- Validação de username e email únicos
- Senha só é alterada se fornecida



