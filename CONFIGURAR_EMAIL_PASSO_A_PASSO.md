# 📧 Como Configurar Email - Passo a Passo Simples

## ⚠️ IMPORTANTE: O sistema funciona SEM email!

Você pode usar o sistema normalmente. Só não vai:
- ❌ Enviar relatórios automáticos por email
- ❌ Enviar alertas por email

**Mas tudo mais funciona perfeitamente!** ✅

---

## Se quiser configurar email depois (opcional):

### 1️⃣ Abra o arquivo `.env`

No Bloco de Notas, abra o arquivo `.env` que está na pasta do projeto.

### 2️⃣ Adicione estas linhas no final:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=senha-de-app-aqui
SMTP_FROM=seu-email@gmail.com
SMTP_USE_TLS=true
```

### 3️⃣ Preencha com seus dados:

**Exemplo:**
```env
SMTP_USER=edemachado@gmail.com
SMTP_PASSWORD=abcdefghijklmnop
SMTP_FROM=edemachado@gmail.com
```

### 4️⃣ Como pegar a senha de app do Gmail:

1. Acesse: https://myaccount.google.com/apppasswords
2. Selecione "Email" → "Outro" → Digite "Absenteismo"
3. Clique em "Gerar"
4. Copie a senha (16 letras, sem espaços)
5. Cole no `SMTP_PASSWORD`

### 5️⃣ Salve o arquivo

Pronto! ✅

---

## 📝 Resumo:

- ✅ Sistema funciona SEM email
- ✅ Você pode usar tudo normalmente
- ✅ Configure email só se quiser relatórios automáticos
- ✅ Pode configurar depois quando quiser

---

**Dúvidas? Deixa o email para depois e usa o sistema normalmente!** 😊

