# Absenteísmo Controller — Security Model

## Estado atual

- Produção operacional com stack conhecida.  
- **PR #4 (S01-A)** — draft: guard de tenant, APIs críticas autenticadas, startup não destrutivo, remoção de `admin/admin123`, clone com origem explícita.  
- **Não mergeado / não publicado** até autorização.

## Princípios

- Autenticação em APIs sensíveis.  
- `client_id` explícito; **sem** fallback `1`.  
- Sem IDOR entre tenants.  
- Admin explícito; sem elevation silenciosa.  
- Startup não zera permissões nem reseeds senhas.

## Perfis-alvo (Épico 4)

Administrador · Médico · RH · SST · Diretoria · (auditoria).

## Controles futuros

Rate limit, lockout, recuperação segura de senha, expiração de sessão, CORS restrito, secrets fora do repo, CSP/headers, auditoria de acesso/exportação.

## Relação com analytics

PRs #5/#6 não abrem endpoint público de produção; shadow local/readonly. Novas APIs de importação (Épico 1) **devem** nascer já sob o modelo do PR #4.
