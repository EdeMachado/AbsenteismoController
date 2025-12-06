# 📧 Configurar Email Corporativo (@grupobiomed.com)

## 🎯 Email: @grupobiomed.com (Google Workspace)

### Passo a Passo Simples:

#### 1️⃣ Abra o arquivo `.env` no Bloco de Notas

#### 2️⃣ Adicione estas linhas no final:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@grupobiomed.com
SMTP_PASSWORD=senha-de-app-aqui
SMTP_FROM=seu-email@grupobiomed.com
SMTP_USE_TLS=true
```

#### 3️⃣ Preencha com seu email:

**Exemplo:**
```env
SMTP_USER=edemachado@grupobiomed.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM=edemachado@grupobiomed.com
```

#### 4️⃣ Como pegar a senha de app:

1. Acesse: https://myaccount.google.com/apppasswords
   - Faça login com seu email @grupobiomed.com

2. Se não aparecer "Senhas de app":
   - Ative verificação em 2 etapas primeiro
   - Acesse: https://myaccount.google.com/security

3. Depois:
   - Selecione "Email"
   - Selecione "Outro (nome personalizado)"
   - Digite: `AbsenteismoController`
   - Clique em "Gerar"

4. Copie a senha gerada:
   - Vai aparecer: `abcd efgh ijkl mnop`
   - Copie tudo junto, sem espaços: `abcdefghijklmnop`

5. Cole no `.env`:
   ```env
   SMTP_PASSWORD=abcdefghijklmnop
   ```

#### 5️⃣ Salve o arquivo (Ctrl+S)

Pronto! ✅

---

## ⚠️ Se não conseguir gerar senha de app:

Algumas empresas bloqueiam senhas de app. Nesse caso:

1. **Fale com o administrador do Google Workspace** da empresa
2. **Peça para liberar** "Senhas de app" para sua conta
3. **OU use** uma conta de serviço criada especificamente para isso

---

## 📝 Exemplo Completo do `.env`:

```env
SECRET_KEY=sua-chave-que-ja-existe
ENVIRONMENT=production

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=edemachado@grupobiomed.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM=edemachado@grupobiomed.com
SMTP_USE_TLS=true
```

---

## ✅ Depois de configurar:

1. Salve o arquivo
2. Reinicie o sistema (se estiver rodando)
3. Pronto! Relatórios e alertas serão enviados automaticamente

---

## 🔒 Segurança:

- ⚠️ NUNCA compartilhe a senha de app
- ⚠️ NUNCA commite o arquivo `.env` no Git
- ✅ Use senha de app (não a senha normal da conta)

---

**Dúvidas? O sistema funciona sem email também! Pode configurar depois.** 😊

