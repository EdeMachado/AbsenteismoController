# 🚀 Guia Rápido - Arquivo .env

## 📝 O que é?

O arquivo `.env` é um arquivo de **configuração** que guarda informações sensíveis como:
- ✅ Senhas
- ✅ Chaves de API  
- ✅ Configurações de email
- ✅ Outras configurações do sistema

## 🔒 Segurança

- ⚠️ **NUNCA** commite o `.env` no Git (já está protegido no `.gitignore`)
- ⚠️ **NÃO** compartilhe o conteúdo do `.env`
- ✅ Use senhas fortes
- ✅ No servidor, crie o `.env` diretamente lá

## 📍 Onde criar?

Na **raiz do projeto** (mesmo nível de `backend/` e `frontend/`):

```
AbsenteismoConverplast/
├── backend/
├── frontend/
├── .env          ← Crie aqui!
└── requirements.txt
```

## 📋 Conteúdo Mínimo

Crie um arquivo `.env` com este conteúdo:

```env
# Email (para relatórios e alertas)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-de-app
SMTP_FROM=seu-email@gmail.com
SMTP_USE_TLS=true

# Chave secreta (já deve existir)
SECRET_KEY=sua-chave-secreta-aqui

# Ambiente
ENVIRONMENT=production
```

## 📧 Configurar Gmail

1. **Ative verificação em 2 etapas:**
   - https://myaccount.google.com/security

2. **Gere Senha de App:**
   - https://myaccount.google.com/apppasswords
   - Selecione "Email" → "Outro" → Digite "AbsenteismoController"
   - **Copie a senha gerada** (16 caracteres)

3. **Use no `.env`:**
   ```env
   SMTP_USER=seu-email@gmail.com
   SMTP_PASSWORD=abcd-efgh-ijkl-mnop  # Senha de app aqui
   ```

## ✅ Verificar se está funcionando

Após criar o `.env`, reinicie o servidor e verifique os logs:

```bash
# No servidor
systemctl restart absenteismocontroller.service
journalctl -u absenteismocontroller.service -n 20
```

Se aparecer "Tarefas em background iniciadas", está funcionando! ✅

## 📚 Mais informações

Veja o arquivo `COMO_CONFIGURAR_EMAIL.md` para detalhes completos.

