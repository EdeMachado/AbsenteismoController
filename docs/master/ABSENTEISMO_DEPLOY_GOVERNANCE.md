# Absenteísmo Controller — Deploy Governance

## Gates obrigatórios antes de qualquer deploy

1. PR revisado e aprovado.  
2. Testes do escopo verdes.  
3. **Backup validado** (checksum + `quick_check`/`integrity_check`).  
4. Plano de rollback escrito.  
5. **Autorização explícita** humana.  
6. Janela e responsável definidos.

## Pipeline alvo (Épico 4)

```text
checkout → testes → backup → deploy artifact → restart
  → health check → smoke test → (falha ⇒ rollback)
```

## Proibições

- `git pull` ad hoc como único processo permanente.  
- Deploy sem backup.  
- Copiar SQLite local para o VPS.  
- Migration sem rollback testado.  
- Merge/deploy automático ao fechar épico.

## Produção (referência operacional)

- App: `/var/www/absenteismo`  
- DB: `/var/www/absenteismo/database/absenteismo.db`  
- Serviço: `absenteismocontroller.service`  
- Backup conhecido validado: ver master plan §2.

## Smoke test mínimo pós-deploy

- Health/login.  
- Tenant `client_id=2` e `4` isolados.  
- Dashboard carrega.  
- Upload desabilitado ou canário conforme release notes.
