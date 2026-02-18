# 💾 GUIA DE BACKUP E RESTORE DO BANCO DE DADOS

## 📋 RESPOSTA RÁPIDA

**SIM, o banco de dados vai junto!** Você só precisa copiar o arquivo `database/absenteismo.db`

---

## 🗄️ TIPO DE BANCO DE DADOS

**SQLite** - Banco de dados em arquivo único
- ✅ **Localização**: `database/absenteismo.db`
- ✅ **Formato**: Arquivo único (fácil de copiar)
- ✅ **Portabilidade**: Funciona em qualquer servidor
- ✅ **Sem configuração**: Não precisa instalar servidor de banco

---

## 📦 O QUE COPIAR PARA PRODUÇÃO

### **1. Arquivo do Banco de Dados** ✅
```
database/absenteismo.db  ← COPIE ESTE ARQUIVO
```

### **2. Pasta de Uploads** (se houver arquivos originais)
```
uploads/  ← Opcional (planilhas já processadas)
```

### **3. Pasta de Logos** (se houver logos cadastrados)
```
frontend/static/logos/  ← Opcional
```

### **4. Pasta de Exports** (se houver relatórios exportados)
```
exports/  ← Opcional
```

---

## 🔄 PROCESSO DE DEPLOY

### **CENÁRIO 1: Primeira vez (sem dados anteriores)**

1. **Copie apenas o código**:
   - Todo o projeto (backend, frontend, etc.)
   - **NÃO copie** `database/absenteismo.db` (será criado vazio)
   
2. **No servidor, o sistema criará**:
   - `database/absenteismo.db` (novo e vazio)
   - Tabelas automaticamente

3. **Você precisará**:
   - Criar empresas novamente
   - Fazer upload das planilhas novamente

---

### **CENÁRIO 2: Manter dados existentes** ✅ **RECOMENDADO**

1. **Antes de fazer deploy, faça backup**:
   ```bash
   # Copie o arquivo do banco
   copy database\absenteismo.db database\absenteismo_backup.db
   ```

2. **No servidor de produção**:
   - Copie todo o projeto
   - **Copie também** `database/absenteismo.db`
   - Coloque na mesma pasta: `database/absenteismo.db`

3. **Resultado**:
   - ✅ Todas as empresas cadastradas
   - ✅ Todos os uploads
   - ✅ Todos os atestados
   - ✅ Todos os mapeamentos customizados
   - ✅ Todas as configurações
   - ✅ Todos os usuários
   - ✅ Todos os logos
   - ✅ Tudo funcionando como antes!

---

## 🛠️ COMO FAZER BACKUP

### **Opção 1: Backup Manual (Simples)**

```bash
# Windows
copy database\absenteismo.db database\absenteismo_backup_20241114.db

# Linux/Mac
cp database/absenteismo.db database/absenteismo_backup_20241114.db
```

### **Opção 2: Script Python (Recomendado)**

Crie um arquivo `backup_banco.py`:

```python
import shutil
from datetime import datetime
import os

# Caminho do banco
db_path = os.path.join("database", "absenteismo.db")
backup_dir = "backups"
os.makedirs(backup_dir, exist_ok=True)

# Nome do backup com data/hora
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = os.path.join(backup_dir, f"absenteismo_backup_{timestamp}.db")

# Copia o banco
if os.path.exists(db_path):
    shutil.copy2(db_path, backup_path)
    print(f"✅ Backup criado: {backup_path}")
    print(f"   Tamanho: {os.path.getsize(backup_path) / 1024 / 1024:.2f} MB")
else:
    print(f"❌ Banco não encontrado: {db_path}")
```

Execute:
```bash
python backup_banco.py
```

---

## 📤 COMO RESTAURAR

### **1. Pare o servidor** (se estiver rodando)

### **2. Substitua o arquivo**
```bash
# Windows
copy database\absenteismo_backup_20241114.db database\absenteismo.db

# Linux/Mac
cp database/absenteismo_backup_20241114.db database/absenteismo.db
```

### **3. Inicie o servidor novamente**
- Os dados estarão restaurados!

---

## ⚠️ IMPORTANTE - ESTRUTURA NECESSÁRIA

### **Pastas que devem existir:**
```
projeto/
├── backend/
├── frontend/
├── database/          ← Deve existir
│   └── absenteismo.db ← Coloque o arquivo aqui
├── uploads/           ← Opcional, mas recomendado
├── exports/           ← Opcional
└── requirements.txt
```

### **Permissões (Linux/Mac):**
```bash
# O banco precisa de permissão de escrita
chmod 664 database/absenteismo.db
chmod 775 database/
```

---

## 🔐 SEGURANÇA - LGPD

### **⚠️ ATENÇÃO:**
- O arquivo `absenteismo.db` contém **TODOS os dados** das empresas
- **NUNCA** commite no Git (já está no `.gitignore`)
- **SEMPRE** faça backup antes de fazer deploy
- **PROTEJA** o arquivo em produção (permissões restritas)

### **Backup Regular:**
Recomenda-se fazer backup:
- ✅ Antes de cada deploy
- ✅ Diariamente (automatizado)
- ✅ Antes de alterações no sistema
- ✅ Após uploads importantes

---

## 📊 CONTEÚDO DO BANCO

O arquivo `absenteismo.db` contém:

1. **Tabela `clients`**: Todas as empresas cadastradas
2. **Tabela `uploads`**: Histórico de planilhas enviadas
3. **Tabela `atestados`**: Todos os registros de atestados
4. **Tabela `users`**: Usuários do sistema
5. **Tabela `configs`**: Configurações do sistema
6. **Tabela `client_column_mappings`**: Mapeamentos customizados
7. **Tabela `client_logos`**: Logos das empresas
8. **Tabela `saved_filters`**: Filtros salvos
9. **Tabela `produtividade`**: Dados de produtividade

**TUDO em um único arquivo!** ✅

---

## 🚀 PROCESSO COMPLETO DE DEPLOY

### **1. BACKUP (no servidor atual)**
```bash
python backup_banco.py
# ou
copy database\absenteismo.db database\absenteismo_backup.db
```

### **2. PREPARAR CÓDIGO**
```bash
# Commit e push do código
git add .
git commit -m "Deploy para produção"
git push
```

### **3. NO SERVIDOR DE PRODUÇÃO**

#### **3.1. Clonar/Baixar código**
```bash
git clone [url-do-repositorio]
# ou
git pull  # se já existe
```

#### **3.2. Copiar banco de dados**
```bash
# Via FTP, SCP, ou método preferido
# Copie: database/absenteismo.db para o servidor
```

#### **3.3. Criar pastas necessárias**
```bash
mkdir -p uploads exports database
```

#### **3.4. Instalar dependências**
```bash
pip install -r requirements.txt
```

#### **3.5. Verificar estrutura**
```
projeto/
├── backend/
├── frontend/
├── database/
│   └── absenteismo.db  ← VERIFIQUE SE ESTÁ AQUI
├── uploads/
├── exports/
└── requirements.txt
```

#### **3.6. Iniciar servidor**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
# ou
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

---

## ✅ CHECKLIST DE DEPLOY

- [ ] Backup do banco feito (`absenteismo.db`)
- [ ] Código commitado e no servidor
- [ ] Arquivo `database/absenteismo.db` copiado para servidor
- [ ] Pastas `uploads/` e `exports/` criadas
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Permissões configuradas (Linux)
- [ ] Servidor iniciado
- [ ] Testado acesso ao sistema
- [ ] Verificado que empresas estão cadastradas
- [ ] Verificado que dados aparecem no dashboard

---

## 🔄 MIGRAÇÃO PARA POSTGRESQL (FUTURO)

Se no futuro quiser migrar para PostgreSQL:

1. **Usar SQLAlchemy** facilita migração
2. **Alterar** `backend/database.py`:
   ```python
   # De:
   SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"
   
   # Para:
   SQLALCHEMY_DATABASE_URL = "postgresql://user:pass@host:5432/dbname"
   ```
3. **Fazer dump do SQLite e importar no PostgreSQL**
4. **Reiniciar sistema**

**Mas por enquanto, SQLite é perfeito!** ✅

---

## 📝 RESUMO

### **✅ SIM, o banco vai junto!**

**Arquivo a copiar**: `database/absenteismo.db`

**Processo**:
1. Copiar código
2. Copiar `database/absenteismo.db`
3. Copiar pastas `uploads/` e `exports/` (opcional)
4. Iniciar servidor
5. **PRONTO!** Todos os dados estarão lá!

**Sem precisar**:
- ❌ Recadastrar empresas
- ❌ Fazer upload novamente
- ❌ Configurar mapeamentos
- ❌ Recriar usuários

---

**Status**: ✅ **BANCO DE DADOS PORTÁTIL - COPIE E USE!**










