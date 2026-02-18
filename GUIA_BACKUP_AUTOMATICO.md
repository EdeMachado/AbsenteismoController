# 📅 GUIA: CONFIGURAR BACKUP AUTOMÁTICO DIÁRIO

Este guia explica como configurar o backup automático do banco de dados para executar diariamente, mesmo quando o servidor não estiver rodando.

---

## 🎯 O QUE SERÁ CONFIGURADO

- ✅ Backup automático **diário** às **02:00**
- ✅ Retenção de **7 dias** (backups antigos são removidos automaticamente)
- ✅ Funciona mesmo quando o servidor não está rodando
- ✅ Logs salvos em `logs/backup.log`

---

## 🚀 OPÇÃO 1: CONFIGURAÇÃO AUTOMÁTICA (RECOMENDADO)

### Passo 1: Execute o Script PowerShell

1. **Clique com botão direito** em `CONFIGURAR_BACKUP_AUTOMATICO.ps1`
2. Escolha **"Executar com PowerShell"** ou **"Executar como Administrador"**
3. Se aparecer aviso de segurança, digite `S` para continuar

### Passo 2: Pronto! ✅

O script vai:
- ✅ Verificar se Python está instalado
- ✅ Criar a tarefa agendada automaticamente
- ✅ Configurar para executar diariamente às 02:00

---

## 🛠️ OPÇÃO 2: CONFIGURAÇÃO MANUAL

### Passo 1: Abrir o Agendador de Tarefas

1. Pressione `Win + R`
2. Digite: `taskschd.msc`
3. Pressione Enter

### Passo 2: Criar Nova Tarefa

1. No painel direito, clique em **"Criar Tarefa..."**
2. Na aba **"Geral"**:
   - **Nome:** `AbsenteismoController_BackupAutomatico`
   - **Descrição:** `Backup automático diário do banco de dados`
   - Marque: **"Executar se o usuário estiver ou não conectado"**
   - Marque: **"Executar com privilégios mais altos"**

### Passo 3: Configurar Trigger (Quando Executar)

1. Vá para a aba **"Gatilhos"**
2. Clique em **"Novo..."**
3. Configure:
   - **Iniciar a tarefa:** `Diariamente`
   - **Hora:** `02:00:00`
   - **Repetir a cada:** `1 dias`
4. Clique em **"OK"**

### Passo 4: Configurar Ação (O Que Executar)

1. Vá para a aba **"Ações"**
2. Clique em **"Novo..."**
3. Configure:
   - **Ação:** `Iniciar um programa`
   - **Programa/script:** Clique em **"Procurar..."** e selecione:
     ```
     C:\Users\Ede Machado\AbsenteismoConverplast\BACKUP_AUTOMATICO.bat
     ```
   - **Iniciar em (opcional):**
     ```
     C:\Users\Ede Machado\AbsenteismoConverplast
     ```
4. Clique em **"OK"**

### Passo 5: Configurar Condições

1. Vá para a aba **"Condições"**
2. Marque: **"Iniciar a tarefa mesmo se o computador estiver em modo de economia de energia"**
3. Desmarque: **"Acordar o computador para executar esta tarefa"**

### Passo 6: Configurar Configurações

1. Vá para a aba **"Configurações"**
2. Marque: **"Permitir execução da tarefa sob demanda"**
3. Marque: **"Executar a tarefa o mais rápido possível após uma inicialização agendada perdida"**
4. Em **"Se a tarefa já estiver em execução:"**, escolha: **"Não iniciar uma nova instância"**

### Passo 7: Salvar

1. Clique em **"OK"**
2. Digite a senha do administrador se solicitado
3. Pronto! ✅

---

## ✅ VERIFICAR SE ESTÁ FUNCIONANDO

### Método 1: Testar Manualmente

1. Abra o **Agendador de Tarefas**
2. Procure por `AbsenteismoController_BackupAutomatico`
3. Clique com botão direito → **"Executar"**
4. Verifique se aparece um novo arquivo em `backups/`

### Método 2: Verificar Logs

1. Abra o arquivo: `logs/backup.log`
2. Deve aparecer uma linha com a data/hora do backup

### Método 3: Verificar Histórico

1. No **Agendador de Tarefas**
2. Clique na tarefa `AbsenteismoController_BackupAutomatico`
3. Vá para a aba **"Histórico"**
4. Veja se há execuções bem-sucedidas

---

## 🔧 AJUSTAR HORÁRIO DO BACKUP

### Opção 1: Pelo Agendador de Tarefas

1. Abra o **Agendador de Tarefas**
2. Procure por `AbsenteismoController_BackupAutomatico`
3. Clique com botão direito → **"Propriedades"**
4. Vá para a aba **"Gatilhos"**
5. Clique duas vezes no gatilho existente
6. Altere o horário
7. Clique em **"OK"**

### Opção 2: Pelo PowerShell

```powershell
# Alterar para 03:00
$task = Get-ScheduledTask -TaskName "AbsenteismoController_BackupAutomatico"
$trigger = $task.Triggers[0]
$trigger.StartBoundary = (Get-Date -Hour 3 -Minute 0 -Second 0).ToString("yyyy-MM-ddTHH:mm:ss")
Set-ScheduledTask -TaskName "AbsenteismoController_BackupAutomatico" -Trigger $trigger
```

---

## 🗑️ REMOVER BACKUP AUTOMÁTICO

### Pelo Agendador de Tarefas

1. Abra o **Agendador de Tarefas**
2. Procure por `AbsenteismoController_BackupAutomatico`
3. Clique com botão direito → **"Excluir"**
4. Confirme

### Pelo PowerShell

```powershell
Unregister-ScheduledTask -TaskName "AbsenteismoController_BackupAutomatico" -Confirm:$false
```

---

## 📋 RESUMO

| Item | Configuração |
|------|--------------|
| **Frequência** | Diário |
| **Horário** | 02:00 (configurável) |
| **Retenção** | 7 dias |
| **Limpeza** | Automática |
| **Logs** | `logs/backup.log` |
| **Funciona offline** | Sim |

---

## ❓ PROBLEMAS COMUNS

### Python não encontrado

**Solução:** Configure o caminho completo do Python no Task Scheduler:
1. Abra as propriedades da tarefa
2. Na aba "Ações", edite a ação
3. Em "Programa/script", coloque o caminho completo:
   ```
   C:\Python3XX\python.exe
   ```
4. Em "Adicionar argumentos", coloque:
   ```
   backup_automatico.py
   ```
5. Em "Iniciar em", coloque o diretório do projeto

### Tarefa não executa

**Verifique:**
1. Se Python está instalado e no PATH
2. Se o caminho do script está correto
3. Se a tarefa está habilitada (não desabilitada)
4. Se o usuário tem permissões de administrador
5. O histórico da tarefa no Agendador de Tarefas

### Backups não são criados

**Verifique:**
1. Se o arquivo `database/absenteismo.db` existe
2. Se a pasta `backups/` tem permissão de escrita
3. O arquivo `logs/backup.log` para ver erros

---

## 📞 SUPORTE

Se tiver problemas, verifique:
- ✅ Logs em `logs/backup.log`
- ✅ Histórico no Agendador de Tarefas
- ✅ Se Python está funcionando: `python --version`

---

**Desenvolvido para AbsenteismoController v2.0**

