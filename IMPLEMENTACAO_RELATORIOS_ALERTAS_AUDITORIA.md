# 🚀 Implementação: Relatórios Automáticos, Alertas e Auditoria

## ✅ O que foi implementado:

### 1. 📧 **Relatórios Automáticos por Email**
- ✅ Modelo `ReportSchedule` para agendamento
- ✅ Sistema de geração e envio de relatórios
- ✅ Agendador em background que verifica e envia automaticamente
- ✅ Suporte a frequências: diária, semanal, mensal
- ✅ Formatos: Excel, PDF (em desenvolvimento)
- ✅ Configuração de emails destinatários
- ✅ API para criar e gerenciar agendamentos

**Como usar:**
1. Configure variáveis de ambiente SMTP:
   - `SMTP_HOST` (ex: smtp.gmail.com)
   - `SMTP_PORT` (ex: 587)
   - `SMTP_USER` (seu email)
   - `SMTP_PASSWORD` (senha do email)
   - `SMTP_FROM` (email remetente)

2. Crie agendamento via API:
   ```
   POST /api/report-schedules
   ```

### 2. 📋 **Histórico de Alterações (Auditoria)**
- ✅ Modelo `AuditLog` para registro de ações
- ✅ Middleware que captura automaticamente ações importantes
- ✅ Registra: CREATE, UPDATE, DELETE, LOGIN, etc.
- ✅ Armazena: usuário, IP, user agent, detalhes da ação
- ✅ API para consultar logs (apenas admin)

**Como usar:**
- Acesse: `GET /api/audit/logs`
- Filtros disponíveis: user_id, client_id, action, resource_type

### 3. ⚠️ **Sistema de Alertas e Notificações**
- ✅ Modelo `Alert` para alertas
- ✅ Modelo `AlertRule` para regras configuráveis
- ✅ Verificação automática de regras em background
- ✅ Envio automático de emails de alerta
- ✅ API para gerenciar alertas e regras

**Tipos de alertas:**
- Limite de dias perdidos excedido
- Taxa de absenteísmo acima do normal
- Tendências de aumento
- Anomalias detectadas

**Como usar:**
1. Configure regras de alerta (via API - será criada interface)
2. Sistema verifica automaticamente a cada minuto
3. Alertas são criados e emails enviados automaticamente

## 📁 Arquivos Criados:

### Backend:
- `backend/models.py` - Novos modelos: AuditLog, ReportSchedule, Alert, AlertRule
- `backend/email_service.py` - Serviço de envio de emails
- `backend/audit_service.py` - Serviço de auditoria
- `backend/alert_service.py` - Serviço de alertas
- `backend/report_scheduler.py` - Agendador de relatórios
- `backend/background_tasks.py` - Tarefas em background

### APIs Criadas:
- `GET /api/audit/logs` - Lista logs de auditoria
- `GET /api/report-schedules` - Lista agendamentos
- `POST /api/report-schedules` - Cria agendamento
- `GET /api/alerts` - Lista alertas
- `POST /api/alerts/{id}/read` - Marca alerta como lido
- `POST /api/alerts/{id}/resolve` - Marca alerta como resolvido
- `POST /api/reports/process-scheduled` - Processa relatórios (admin)

## ⚙️ Configuração Necessária:

### Variáveis de Ambiente (.env):
```env
# Email (obrigatório para relatórios e alertas)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu-email@gmail.com
SMTP_PASSWORD=sua-senha-app
SMTP_FROM=seu-email@gmail.com
SMTP_USE_TLS=true
```

**Nota para Gmail:**
- Use "Senha de App" ao invés da senha normal
- Ative verificação em 2 etapas
- Gere senha de app em: https://myaccount.google.com/apppasswords

## 🔄 Próximos Passos (Frontend):

1. **Página de Auditoria** (`/auditoria.html`)
   - Tabela de logs
   - Filtros por usuário, empresa, ação
   - Exportação de logs

2. **Página de Relatórios** (`/relatorios_automaticos.html`)
   - Lista de agendamentos
   - Formulário para criar/editar
   - Status de envios

3. **Dashboard de Alertas** (`/alertas.html`)
   - Lista de alertas não lidos
   - Gráficos de alertas por severidade
   - Configuração de regras

## 🧪 Testar:

1. **Testar Email:**
   ```python
   from backend.email_service import EmailService
   service = EmailService()
   service.send_email(
       to_emails=["teste@exemplo.com"],
       subject="Teste",
       body_html="<h1>Teste</h1>"
   )
   ```

2. **Criar Alerta de Teste:**
   ```python
   from backend.alert_service import AlertService
   from backend.database import SessionLocal
   db = SessionLocal()
   service = AlertService(db)
   service.create_alert(
       client_id=1,
       tipo="teste",
       titulo="Alerta de Teste",
       mensagem="Este é um teste"
   )
   ```

3. **Verificar Logs:**
   - Acesse: `GET /api/audit/logs` (como admin)

## 📝 Notas Importantes:

- ⚠️ O sistema de email precisa estar configurado para funcionar
- ⚠️ Tarefas em background rodam a cada 1 minuto
- ⚠️ Relatórios PDF ainda não estão completamente implementados
- ⚠️ Interface frontend ainda precisa ser criada

## 🎯 Status:

- ✅ Backend completo
- ✅ APIs funcionando
- ✅ Tarefas em background ativas
- ⏳ Frontend (próxima etapa)

