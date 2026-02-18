# ⚡ CONFIGURAÇÃO RÁPIDA - BACKUP AUTOMÁTICO

## 🚀 OPÇÃO 1: AUTOMÁTICA (Recomendado)

### Passo a Passo:

1. **Clique com botão direito** em `CONFIGURAR_BACKUP_AUTOMATICO.ps1`
2. Escolha **"Executar com PowerShell"** 
3. Se pedir permissão de administrador, clique **"Sim"**
4. Se aparecer aviso de política de execução, digite `S` para continuar
5. Pronto! ✅

**A tarefa será criada automaticamente para executar diariamente às 02:00**

---

## 🛠️ OPÇÃO 2: MANUAL (Passo a Passo)

### 1. Abrir Agendador de Tarefas
- Pressione `Win + R`
- Digite: `taskschd.msc`
- Enter

### 2. Criar Nova Tarefa
- Clique em **"Criar Tarefa..."** (não "Criar Tarefa Básica")

### 3. Aba "Geral"
- **Nome:** `AbsenteismoController_BackupAutomatico`
- **Descrição:** `Backup automático diário do banco de dados`
- ✅ Marque: **"Executar se o usuário estiver ou não conectado"**
- ✅ Marque: **"Executar com privilégios mais altos"**

### 4. Aba "Gatilhos"
- Clique em **"Novo..."**
- **Iniciar a tarefa:** `Diariamente`
- **Hora:** `02:00:00`
- **Repetir a cada:** `1 dias`
- Clique em **"OK"**

### 5. Aba "Ações"
- Clique em **"Novo..."**
- **Ação:** `Iniciar um programa`
- **Programa/script:** 
  ```
  C:\Users\Ede Machado\AbsenteismoConverplast\BACKUP_AUTOMATICO.bat
  ```
- **Iniciar em (opcional):**
  ```
  C:\Users\Ede Machado\AbsenteismoConverplast
  ```
- Clique em **"OK"**

### 6. Aba "Condições"
- ✅ Marque: **"Iniciar a tarefa mesmo se o computador estiver em modo de economia de energia"**
- ❌ Desmarque: **"Acordar o computador para executar esta tarefa"**

### 7. Aba "Configurações"
- ✅ Marque: **"Permitir execução da tarefa sob demanda"**
- ✅ Marque: **"Executar a tarefa o mais rápido possível após uma inicialização agendada perdida"**
- **Se a tarefa já estiver em execução:** `Não iniciar uma nova instância`

### 8. Salvar
- Clique em **"OK"**
- Digite a senha do administrador se solicitado
- Pronto! ✅

---

## ✅ TESTAR

1. Abra o **Agendador de Tarefas**
2. Procure por `AbsenteismoController_BackupAutomatico`
3. Clique com botão direito → **"Executar"**
4. Verifique se aparece um novo arquivo em `backups/` com prefixo `auto_`

---

## 📋 RESUMO

| Item | Configuração |
|------|--------------|
| **Frequência** | Diário |
| **Horário** | 02:00 |
| **Retenção** | 7 dias (limpeza automática) |
| **Logs** | `logs/backup.log` |
| **Funciona offline** | Sim |

---

**Pronto! O backup será executado automaticamente todos os dias às 02:00**

