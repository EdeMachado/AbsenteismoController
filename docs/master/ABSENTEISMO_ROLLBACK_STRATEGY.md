# Absenteísmo Controller — Rollback Strategy

## Princípios

- Rollback é requisito de release, não improviso.  
- Preferir reverter artefato de aplicação **sem** tocar no banco, quando possível.  
- Qualquer mudança de schema exige backup prévio + migration reversível.

## Cenários

### A) Regressão de código (sem migration)

1. Redeploy da versão anterior (tag/commit conhecido).  
2. Restart `absenteismocontroller.service`.  
3. Health + smoke.  
4. Registrar incidente.

### B) Migration aplicada com erro

1. **Não** improvisar SQL em produção.  
2. Executar down migration testada **ou** restaurar DB a partir do backup pré-deploy.  
3. Redeploy app compatível com o schema restaurado.  
4. Validar integridade (`quick_check`/`integrity_check`).

### C) Corrupção / perda de dados

1. Isolar escrita (manutenção).  
2. Restaurar backup validado (ex.: snapshot com SHA conhecido).  
3. Verificar checksum.  
4. Smoke + amostragem agregada (sem expor PII em tickets).

## Evidências a guardar

- SHA do backup usado.  
- Commit/tag do app.  
- Horário UTC.  
- Operador.  
- Resultado dos checks.

## O que não fazer

- Restaurar backup “por cima” sem checksum.  
- Misturar DB de homologação com produção.  
- Apagar backups recentes após falha.
