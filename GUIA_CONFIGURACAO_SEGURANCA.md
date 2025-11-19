# Guia de Configuração de Segurança

Este guia explica como configurar corretamente as variáveis de ambiente e garantir a segurança do sistema.

## 🔐 Configuração de SECRET_KEY

### Passo 1: Criar arquivo .env

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   copy .env.example .env
   ```

2. Ou crie manualmente um arquivo `.env` na raiz do projeto com o seguinte conteúdo:
   ```env
   SECRET_KEY=sua-chave-secreta-aqui
   ```

### Passo 2: Gerar uma SECRET_KEY segura

Execute o seguinte comando Python para gerar uma chave segura:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie a chave gerada e cole no arquivo `.env`:
```env
SECRET_KEY=chave-gerada-aqui
```

### Passo 3: Verificar configuração

Execute o script de validação:
```bash
python validar_seguranca.py
```

O script verificará:
- ✅ Se SECRET_KEY está configurada
- ✅ Se o arquivo .env existe
- ✅ Se .env está no .gitignore
- ✅ Se as validações de segurança estão funcionando

## 🛡️ Garantir que .env não seja commitado

### Verificar .gitignore

Certifique-se de que o arquivo `.gitignore` contém:
```
.env
.env.local
.env.*.local
```

### Verificar se .env está no Git

Se você já commitou o arquivo .env por engano:
```bash
# Remove do Git mas mantém o arquivo local
git rm --cached .env

# Commit a remoção
git commit -m "Remove .env do controle de versão"
```

## 🔒 Teste de Isolamento de Dados

Execute o script de teste de isolamento:
```bash
python test_isolamento_dados.py
```

Este script:
- Cria clientes de teste
- Cria dados para cada cliente
- Verifica se os dados estão isolados corretamente
- Valida que um cliente não vê dados de outro

## 📋 Checklist de Segurança

Antes de colocar em produção, verifique:

- [ ] SECRET_KEY definida no arquivo .env
- [ ] Arquivo .env está no .gitignore
- [ ] SECRET_KEY tem pelo menos 32 caracteres
- [ ] Script `validar_seguranca.py` passa sem erros
- [ ] Script `test_isolamento_dados.py` passa sem erros
- [ ] Logs de segurança estão sendo gerados
- [ ] Rate limiting está ativo
- [ ] Headers de segurança estão configurados

## 🚨 Em Produção

### Variáveis de Ambiente no Servidor

Em produção, configure as variáveis de ambiente diretamente no servidor:

**Linux/Unix:**
```bash
export SECRET_KEY="sua-chave-secreta-aqui"
```

**Windows:**
```cmd
set SECRET_KEY=sua-chave-secreta-aqui
```

**Docker:**
```yaml
environment:
  - SECRET_KEY=${SECRET_KEY}
```

**Serviços Cloud:**
- Configure via painel de controle do serviço
- Use serviços de gerenciamento de secrets (AWS Secrets Manager, Azure Key Vault, etc.)

### Rotação de SECRET_KEY

Para rotacionar a SECRET_KEY em produção:

1. Gere uma nova chave
2. Atualize a variável de ambiente
3. Reinicie o serviço
4. **IMPORTANTE:** Todos os tokens JWT existentes serão invalidados
   - Usuários precisarão fazer login novamente

## 📝 Logs de Segurança

O sistema gera logs de segurança em `logs/security.log`:

- Tentativas de login falhadas
- Rate limiting excedido
- Tentativas de acesso não autorizado
- Alterações em configurações sensíveis

Monitore regularmente este arquivo em produção.

## 🔍 Troubleshooting

### SECRET_KEY não está sendo carregada

1. Verifique se o arquivo `.env` existe na raiz do projeto
2. Verifique se `python-dotenv` está instalado: `pip install python-dotenv`
3. Execute `validar_seguranca.py` para diagnóstico

### Aviso sobre SECRET_KEY em desenvolvimento

Se você ver o aviso:
```
UserWarning: SECRET_KEY não definida em variável de ambiente!
```

Isso é normal em desenvolvimento, mas **NÃO deve aparecer em produção**.

### Teste de isolamento falha

Se o teste de isolamento falhar:
1. Verifique os logs em `logs/errors.log`
2. Execute `python test_isolamento_dados.py` novamente
3. Verifique se há dados órfãos no banco de dados

## 📚 Referências

- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [LGPD - Lei Geral de Proteção de Dados](https://www.gov.br/cidadania/pt-br/acesso-a-informacao/lgpd)



