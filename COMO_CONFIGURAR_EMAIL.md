# 📧 Como Configurar Email no Sistema

## 🎯 Objetivo

Configurar o envio automático de:
- ✅ Relatórios por email
- ✅ Alertas e notificações

## 📋 Passo a Passo

### 1️⃣ Criar arquivo `.env`

Na raiz do projeto, crie um arquivo chamado `.env` (ou copie do `.env.example`):

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2️⃣ Configurar Gmail (Recomendado)

#### Opção A: Gmail Pessoal

1. **Ative verificação em 2 etapas:**
   - Acesse: https://myaccount.google.com/security
   - Ative "Verificação em duas etapas"

2. **Gere uma Senha de App:**
   - Acesse: https://myaccount.google.com/apppasswords
   - Selecione "Email" e "Outro (nome personalizado)"
   - Digite: "AbsenteismoController"
   - Clique em "Gerar"
   - **Copie a senha gerada** (16 caracteres, sem espaços)

3. **Configure no `.env`:**
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=seu-email@gmail.com
   SMTP_PASSWORD=abcd-efgh-ijkl-mnop  # Senha de app gerada
   SMTP_FROM=seu-email@gmail.com
   SMTP_USE_TLS=true
   ```

#### Opção B: Gmail Empresarial (Google Workspace)

Mesmo processo, mas use o email corporativo:
```env
SMTP_USER=seu-email@empresa.com
SMTP_FROM=seu-email@empresa.com
```

### 3️⃣ Configurar Outlook/Hotmail

```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=seu-email@outlook.com
SMTP_PASSWORD=sua-senha
SMTP_FROM=seu-email@outlook.com
SMTP_USE_TLS=true
```

### 4️⃣ Configurar Outros Provedores

| Provedor | SMTP_HOST | SMTP_PORT |
|----------|-----------|-----------|
| Yahoo | smtp.mail.yahoo.com | 587 |
| Zoho | smtp.zoho.com | 587 |
| SendGrid | smtp.sendgrid.net | 587 |
| Mailgun | smtp.mailgun.org | 587 |

### 5️⃣ Testar Configuração

Após configurar, reinicie o servidor e teste:

```python
# No Python (ou via API)
from backend.email_service import EmailService

service = EmailService()
if service.is_configured():
    success = service.send_email(
        to_emails=["seu-email@teste.com"],
        subject="Teste",
        body_html="<h1>Teste de email</h1>"
    )
    if success:
        print("✅ Email enviado com sucesso!")
    else:
        print("❌ Erro ao enviar email")
else:
    print("⚠️ Email não configurado")
```

## 🔒 Segurança

### ⚠️ IMPORTANTE:

1. **NUNCA commite o arquivo `.env` no Git**
   - Ele já está no `.gitignore`
   - Contém informações sensíveis

2. **No servidor:**
   - Crie o arquivo `.env` diretamente no servidor
   - Não envie por email ou mensagem
   - Use conexão segura (SSH) para editar

3. **Senhas:**
   - Use senhas fortes
   - Para Gmail, SEMPRE use "Senha de App"
   - Nunca use a senha principal da conta

## 🧪 Testar no Servidor

Após fazer deploy:

1. Crie o arquivo `.env` no servidor:
   ```bash
   cd /var/www/absenteismo
   nano .env
   ```

2. Cole as configurações

3. Reinicie o serviço:
   ```bash
   systemctl restart absenteismocontroller.service
   ```

4. Verifique os logs:
   ```bash
   journalctl -u absenteismocontroller.service -n 50
   ```

## ❓ Problemas Comuns

### "Erro ao enviar email"
- ✅ Verifique se a senha está correta
- ✅ Para Gmail, use senha de app (não a senha normal)
- ✅ Verifique se a verificação em 2 etapas está ativa
- ✅ Teste a conexão SMTP manualmente

### "SMTP não configurado"
- ✅ Verifique se o arquivo `.env` existe
- ✅ Verifique se as variáveis estão corretas
- ✅ Reinicie o servidor após criar/editar `.env`

### "Timeout ao conectar"
- ✅ Verifique firewall/proxy
- ✅ Teste se a porta 587 está aberta
- ✅ Tente usar porta 465 com SSL (mude SMTP_USE_TLS para false)

## 📞 Suporte

Se tiver problemas, verifique:
1. Logs do sistema: `journalctl -u absenteismocontroller.service`
2. Teste de conexão SMTP
3. Configurações do provedor de email

