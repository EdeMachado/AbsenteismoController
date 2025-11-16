# 📖 GUIA DE USO DAS MELHORIAS IMPLEMENTADAS

## 🎯 VISÃO GERAL

Este guia explica como usar e monitorar as melhorias de robustez implementadas no sistema.

---

## 📋 1. SISTEMA DE LOGGING

### **Localização dos Logs**

Os logs são salvos automaticamente na pasta `logs/`:

- `logs/app.log` - Logs gerais da aplicação
- `logs/errors.log` - Apenas erros
- `logs/security.log` - Eventos de segurança (formato JSON)
- `logs/audit.log` - Auditoria de ações (formato JSON)

### **Rotação Automática**

- Os logs são rotacionados automaticamente quando atingem 10MB
- Mantém os últimos 5 backups de cada log
- Formato: `app.log`, `app.log.1`, `app.log.2`, etc.

### **Como Visualizar**

```bash
# Ver logs em tempo real
tail -f logs/app.log

# Ver apenas erros
tail -f logs/errors.log

# Ver eventos de segurança
tail -f logs/security.log

# Ver auditoria
tail -f logs/audit.log
```

### **Exemplo de Log de Auditoria (JSON)**

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "level": "INFO",
  "action": "login",
  "user_id": 1,
  "client_id": 2,
  "ip_address": "192.168.1.100",
  "message": "AUDIT: login"
}
```

---

## 🏥 2. HEALTH CHECK

### **Endpoint**

```
GET /api/health
```

### **Resposta**

```json
{
  "status": "healthy|degraded|unhealthy",
  "version": "2.0.0",
  "timestamp": "2024-01-01T12:00:00",
  "checks": {
    "database": {
      "status": "ok",
      "message": "Conexão com banco de dados funcionando"
    },
    "database_integrity": {
      "status": "ok",
      "message": "Integridade do banco verificada"
    },
    "disk": {
      "status": "ok",
      "total_gb": 500.0,
      "free_gb": 200.0,
      "used_percent": 60.0,
      "message": "60.0% usado"
    },
    "memory": {
      "status": "ok",
      "total_gb": 16.0,
      "available_gb": 8.0,
      "used_percent": 50.0,
      "message": "50.0% usado"
    },
    "paths": {
      "database": {"status": "ok", "path": "..."},
      "uploads": {"status": "ok", "path": "..."},
      "exports": {"status": "ok", "path": "..."},
      "logs": {"status": "ok", "path": "..."}
    }
  }
}
```

### **Status Possíveis**

- `healthy` - Sistema funcionando normalmente
- `degraded` - Algum problema detectado, mas sistema operacional
- `unhealthy` - Problema crítico detectado

### **Como Usar**

```bash
# Via curl
curl http://localhost:8000/api/health

# Via navegador
http://localhost:8000/api/health
```

### **Monitoramento**

Configure ferramentas de monitoramento (ex: Nagios, Zabbix) para verificar este endpoint periodicamente.

---

## 💾 3. BACKUP AUTOMÁTICO

### **Configuração Automática**

- ✅ Backup diário às **02:00** (horário do servidor)
- ✅ Retenção de **7 dias** de backups
- ✅ Máximo de **30 backups** mantidos
- ✅ Backup antes de **uploads críticos**

### **Localização**

Backups salvos em: `backups/absenteismo_backup_YYYYMMDD_HHMMSS.db`

### **Backup Manual**

```bash
# Via script Python
python backup_banco.py

# Listar backups disponíveis
python backup_banco.py listar
```

### **Restaurar Backup**

```bash
# 1. Pare o servidor
# 2. Copie o backup para o lugar do banco
cp backups/absenteismo_backup_20240101_020000.db database/absenteismo.db
# 3. Reinicie o servidor
```

### **Verificar Backups**

Os logs de backup são salvos em `logs/app.log`:

```
INFO: Backup criado: absenteismo_backup_20240101_020000.db (15.23 MB) em 234.56ms
```

---

## ✅ 4. VALIDAÇÃO DE DADOS

### **Endpoint de Validação**

```
GET /api/validate/{client_id}
```

**Requer autenticação** (token JWT)

### **Resposta**

```json
{
  "client_id": 2,
  "valid": true,
  "issues": [],
  "stats": {
    "total_uploads": 10,
    "total_atestados": 500,
    "uploads_sem_atestados": 0,
    "atestados_orfãos": 0
  }
}
```

### **Tipos de Problemas Detectados**

- ⚠️ **Warning**: Uploads sem atestados associados
- ❌ **Error**: Atestados com upload_id inválido

### **Como Usar**

```bash
# Via curl (com token)
curl -H "Authorization: Bearer SEU_TOKEN" \
     http://localhost:8000/api/validate/2
```

### **Validação Automática**

A validação de regras de negócio é executada automaticamente durante uploads:
- Datas (retorno não pode ser anterior a afastamento)
- Dias atestados (0-365 dias)
- Horas perdidas (0-8760 horas)

Problemas são registrados em `logs/app.log` como warnings.

---

## 📤 5. UPLOAD COM TIMEOUT

### **Configurações**

- **Tamanho máximo**: 50MB (configurável)
- **Timeout**: 5 minutos (300 segundos)
- **Upload em chunks**: 8KB por vez

### **Comportamento**

- ✅ Validação de extensão (.xlsx, .xls)
- ✅ Validação de tamanho antes e durante upload
- ✅ Timeout automático se upload demorar muito
- ✅ Limpeza automática de arquivos parciais em caso de erro

### **Mensagens de Erro**

- `413` - Arquivo muito grande
- `408` - Timeout no upload
- `400` - Formato inválido

### **Logs**

Todos os uploads são registrados em `logs/app.log`:

```
INFO: Iniciando upload de planilha para cliente 2
INFO: Arquivo salvo: 20240101_120000_planilha.xlsx (2.5MB)
INFO: Upload concluído: 500 registros processados em 1234.56ms
```

---

## 📊 6. MIDDLEWARE DE LOGGING

### **O Que É Registrado**

Todas as requisições HTTP são registradas automaticamente:

- Método HTTP (GET, POST, etc.)
- URL e parâmetros
- IP do cliente
- User-Agent
- Tempo de resposta
- Status code

### **Headers Adicionados**

Todas as respostas incluem:

```
X-Response-Time: 123.45ms
```

### **Logs de Performance**

Requisições que demoram mais de 5 segundos são registradas como warning:

```
WARNING: Requisição lenta: 5234.56ms
```

### **Logs de Segurança**

Erros 401 (não autorizado) e 403 (proibido) são registrados em `logs/security.log`.

---

## 🔌 7. POOL DE CONEXÕES

### **Configuração**

- **Pool base**: 10 conexões
- **Overflow**: até 20 conexões extras
- **Pre-ping**: Verifica conexões antes de usar
- **Reciclagem**: Conexões recicladas após 1 hora

### **Benefícios**

- ✅ Melhor performance em alta concorrência
- ✅ Menos overhead de criação de conexões
- ✅ Detecção automática de conexões quebradas

### **Monitoramento**

O pool é gerenciado automaticamente pelo SQLAlchemy. Não requer configuração adicional.

---

## 🧪 8. TESTE DO SISTEMA

### **Script de Teste**

Execute o script de teste para verificar se tudo está funcionando:

```bash
python test_system.py
```

### **O Que É Testado**

1. ✅ Diretório de logs
2. ✅ Diretório de backups
3. ✅ Banco de dados
4. ✅ Módulos do sistema
5. ✅ Health check endpoint
6. ✅ Dependências instaladas

---

## 📝 9. MANUTENÇÃO

### **Limpeza de Logs Antigos**

Os logs são rotacionados automaticamente, mas você pode limpar manualmente:

```bash
# Remover logs com mais de 30 dias
find logs/ -name "*.log.*" -mtime +30 -delete
```

### **Limpeza de Backups Antigos**

Os backups são limpos automaticamente (7 dias), mas você pode verificar:

```bash
# Listar backups
python backup_banco.py listar

# Remover backups manualmente (se necessário)
rm backups/absenteismo_backup_YYYYMMDD_HHMMSS.db
```

### **Monitoramento de Espaço em Disco**

Use o health check para monitorar espaço em disco:

```bash
curl http://localhost:8000/api/health | jq '.checks.disk'
```

Alerta automático se uso > 90%.

---

## 🚨 10. TROUBLESHOOTING

### **Problema: Logs não estão sendo criados**

**Solução:**
1. Verifique se a pasta `logs/` existe e tem permissão de escrita
2. Verifique os logs do sistema (stderr) para erros
3. Reinicie o servidor

### **Problema: Backup automático não está funcionando**

**Solução:**
1. Verifique se o servidor está rodando (backup só funciona com servidor ativo)
2. Verifique os logs em `logs/app.log` para erros
3. Execute backup manual: `python backup_banco.py`

### **Problema: Health check retorna erro**

**Solução:**
1. Verifique os logs em `logs/app.log`
2. Verifique se todas as dependências estão instaladas: `pip install -r requirements.txt`
3. Verifique se o banco de dados existe e está acessível

### **Problema: Upload falha com timeout**

**Solução:**
1. Verifique o tamanho do arquivo (máximo 50MB)
2. Verifique a conexão de rede
3. Tente novamente com arquivo menor

---

## 📞 SUPORTE

Para mais informações, consulte:
- `MELHORIAS_IMPLEMENTADAS.md` - Documentação técnica completa
- `SUGESTOES_MELHORIAS_ROBUSTEZ.md` - Lista de melhorias propostas
- Logs em `logs/app.log` - Informações detalhadas do sistema

---

**Última atualização:** 2024-01-01

