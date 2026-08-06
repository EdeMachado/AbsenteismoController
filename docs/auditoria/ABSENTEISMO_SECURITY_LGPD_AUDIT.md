# ABSENTEISMOCONTROLLER — SECURITY & LGPD AUDIT

## Classificação

| Severidade | Significado |
|------------|-------------|
| Crítico | Exposição/alteração indevida de dados sensíveis ou cross-tenant |
| Alto | Compromete autenticação/autorização ou superfície ampla |
| Médio | Configuração frágil / defesa em profundidade |
| Baixo / Info | Higiene e hardening |

---

## Achados

### ABS-SEC-001 / ABS-LGPD-001 — APIs sensíveis sem autenticação (Crítico / P0)
**Descrição:** Endpoints que leem/escrevem atestados, clientes, uploads, produtividade, perfil de funcionário e mapeamentos aceitam chamadas sem JWT.  
**Evidência:** Rotas em `backend/main.py` sem `Depends(get_current_*)` — upload, DELETE upload, CRUD dados, CRUD clientes (várias), produtividade, `/api/funcionario/perfil`, análises, preview, etc.  
**Impacto:** Quem souber/adivinhar `client_id` (inteiro sequencial) acessa CID, diagnóstico, CPF, nomes.  
**Recomendação:** Exigir auth em todas as rotas `/api/*` exceto login, health e landing públicas. Validar `validar_acesso_client_id` em toda leitura/escrita.

### ABS-SEC-002 — CORS `allow_origins=["*"]` + credentials (Alto / P0)
**Arquivo:** `main.py` ~105  
**Recomendação:** Lista explícita do domínio de produção.

### ABS-SEC-003 — Credencial padrão `admin` / `admin123` (Crítico / P0)
**Arquivo:** `main.py` seed no startup  
**Recomendação:** Remover seed em produção; forçar troca; bloquear se `ENVIRONMENT=production`.

### ABS-SEC-004 — `User.client_id = NULL` = acesso a todos os tenants (Crítico / P0)
**Arquivo:** `validar_acesso_client_id`; startup força a maioria dos usuários para NULL; exceção hardcoded “Nilceia” → client 2  
**Impacto:** Quase todos os usuários não-admin têm visão cross-empresa.  
**Recomendação:** Negar por padrão; admin explícito; remover hardcode de pessoa.

### ABS-SEC-005 — JWT em `localStorage` (Alto / P1)
XSS = roubo de sessão. Preferir cookie HttpOnly Secure SameSite (médio prazo).

### ABS-SEC-006 — `auth.js` deletado no working tree (Crítico operacional / P0)
Páginas referenciam `/static/js/auth.js`. Sem o arquivo, checagens client-side e layout quebram. Restaurar do Git imediatamente.

### ABS-SEC-007 — `GET /api/backup/list` sem auth (Alto / P0)
Enumera backups; risco informacional e preparação para exfiltração.

### ABS-SEC-008 — SECRET_KEY ausente gera chave aleatória (Alto / P0)
Tokens inválidos a cada restart; se fraca/antiga, forge. `validar_seguranca.py` detecta chave hardcoded histórica.

### ABS-SEC-009 — Export autenticado sem checagem de tenant (Médio / P1)
Usuário restrito pode exportar outro `client_id` se informar o ID.

### ABS-SEC-010 — CSP com `unsafe-inline` e `unsafe-eval` (Médio / P2)
Reduz proteção XSS.

### ABS-SEC-011 — Rate limit apenas in-process (Baixo / P2)
Não compartilha entre workers Gunicorn.

### ABS-LGPD-002 — Dados clínicos amplos em `Atestado` + `dados_originais` JSON (Alto / P0)
CID, diagnóstico, CPF, JSON bruto da planilha. Sem base legal/consentimento modelado; sem minimização.

### ABS-LGPD-003 — Trilha de auditoria DB não operacional (Alto / P1)
Modelo `AuditLog` + `AuditService` existem; **não são usados** nas rotas. Logs em arquivo são parciais e podem conter dados.

### ABS-LGPD-004 — Sem segregação RH vs saúde (Alto / P1)
Qualquer usuário do tenant (ou todos, se NULL) vê CID/diagnóstico. Não há perfil médico separado.

### ABS-LGPD-005 — INSS schema com `parecer_medico` (Info / P2)
Ainda sem API; risco futuro se exposto sem controle.

---

## Controles positivos observados

- bcrypt rounds=12  
- Middleware bloqueia paths sensíveis (`.env`, `.db`)  
- Validação de upload em `security.py`  
- Isolamento por `Upload.client_id` quando filtros são aplicados  
- Script `validar_seguranca.py` e docs LGPD/ISO na raiz  

---

## Conclusão LGPD

O sistema trata **dados de saúde** (CID/diagnóstico) e **PII**, mas a superfície de API aberta + modelo de permissão permissivo **não atendem** requisitos mínimos de confidencialidade multiempresa para operação em produção com múltiplos clientes.
