# 🚀 Como Ver a Correção do Gráfico TOP CIDs por Setor

## ✅ OPÇÃO 1: Testar Localmente (Rápido - 1 minuto)

### 1. Iniciar o Sistema Localmente

```powershell
cd "C:\Users\Ede Machado\AbsenteismoConverplast"
python -m uvicorn backend.main:app --reload --port 8000
```

**OU** clique duas vezes em: `INICIAR_SISTEMA.bat`

### 2. Acessar no Navegador

Abra: `http://localhost:8000`

### 3. Ir para o Dashboard

- Clique em "Dashboard" no menu lateral
- Role a página até encontrar "Top CIDs por Setor"
- **Agora você verá um GRÁFICO DE BARRAS** ao invés de cards!

---

## 🌐 OPÇÃO 2: Atualizar no Servidor de Produção

### PASSO 1: Fazer Commit e Push (no seu computador)

Execute o script que acabei de criar:

**Clique duas vezes em:** `COMMIT_CORRECAO_GRAFICO.bat`

Isso vai:
- ✅ Adicionar os arquivos corrigidos ao Git
- ✅ Fazer commit com a mensagem
- ✅ Fazer push para o repositório

### PASSO 2: Atualizar no Servidor

**Se você usa Git no servidor:**

Acesse o servidor via SSH e execute:

```bash
cd /caminho/do/seu/sistema  # ex: ~/domains/absenteismocontroller.com.br/public_html/absenteismo
git pull origin main
```

**Se você não usa Git no servidor:**

Você precisa copiar manualmente os 2 arquivos:

1. `frontend/index.html`
2. `frontend/static/js/dashboard.js`

Para o servidor via FTP ou SSH.

### PASSO 3: Recarregar o Sistema no Servidor

```bash
# Se usar Gunicorn/supervisor, reinicie:
sudo systemctl restart absenteismo
# OU
sudo supervisorctl restart absenteismo
```

### PASSO 4: Ver no Site

Acesse: `https://www.absenteismocontroller.com.br`

- Vá para Dashboard
- Role até "Top CIDs por Setor"
- **Agora é um gráfico de barras!**

---

## 🔍 O QUE FOI CORRIGIDO:

✅ Transformado cards em gráfico de barras horizontal
✅ Gráfico mostra top 3 CIDs de cada setor agrupados
✅ Tooltips informativos ao passar o mouse
✅ Visual profissional e limpo
✅ Responsivo e otimizado

---

## ⚡ TESTE RÁPIDO LOCAL (Recomendado antes da apresentação!)

1. Execute: `INICIAR_SISTEMA.bat`
2. Abra: `http://localhost:8000`
3. Veja o gráfico corrigido
4. Se estiver ok, faça o deploy para produção

---

## 🆘 Precisa de ajuda?

Se tiver dúvidas sobre como acessar o servidor ou fazer o deploy, me avise!



