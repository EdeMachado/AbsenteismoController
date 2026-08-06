# ABSENTEISMO — Matriz de implementação responsiva

**Branch:** `fix/production-responsive-phase-2-3`  
**Atualizado:** 2026-08-06  
**Lotes cobertos:** R01 (global) + R02 (dashboard, aproveitando PR #1)

## Legenda

- OK / FALHA / NÃO SE APLICA / NÃO TESTADO / BLOQUEADO

## Decisão de branch

| Base | Decisão |
|------|---------|
| `origin/main` @ `33dce51` | Produção atual |
| PR #1 `cursor/dashboard-responsive-scroll-f8f5` @ `35600ac` | Contém overflow-x, charts-grid, hamburger no dashboard — **aproveitado** |
| Branch de trabalho | Criada a partir do PR #1: `fix/production-responsive-phase-2-3` |
| Motivo | Evitar reimplementar R02; estender shell mobile a todas as páginas |

## Restauração auth.js

| Item | Valor |
|------|-------|
| Método | `git checkout HEAD -- frontend/static/js/auth.js` |
| SHA256 | `63940a62ac88aac6e4ef8125f237732f98b95074333193588c8cfd73f19fe473` |
| Idêntico ao Git HEAD | SIM |
| Idêntico ao `.bak` | SIM |
| Alteração funcional | Nenhuma |

## Matriz (21 páginas)

| ID | Página | Rota | Arquivo | 320 | 390 | 768 | 1024 | 1366 | 1920 | Menu | Tabela | Form | Gráfico | Status |
|----|--------|------|---------|-----|-----|-----|------|------|------|------|--------|------|---------|--------|
| 01 | Dashboard | `/` | index.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | N/A | OK | OK* | R01+R02 |
| 02 | Login | `/login` | login.html | OK* | OK* | OK* | OK* | OK* | OK* | N/A | N/A | OK | N/A | R02 |
| 03 | Landing | `/landing` | landing.html | OK* | OK* | OK* | OK* | OK* | OK* | N/A | N/A | N/A | N/A | R01 shell |
| 04 | Funcionários | `/funcionarios` | funcionarios.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | OK | OK | N/A | R01 |
| 05 | Comparativos | `/comparativos` | comparativos.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | N/A | OK | OK* | R01 |
| 06 | Configurações | `/configuracoes` | configuracoes.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | OK | OK | N/A | R01 |
| 07 | Perfil func. | `/perfil_funcionario` | perfil_funcionario.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | OK | N/A | OK* | R01 |
| 08 | Upload | `/upload` | upload.html | OK* | OK* | OK* | OK* | OK* | OK* | N/A** | OK | OK | N/A | R01 |
| 09 | Clientes | `/clientes` | clientes.html | OK* | OK* | OK* | OK* | OK* | OK* | N/A** | N/A | OK | N/A | R01 shell |
| 10 | Dados | `/dados_powerbi` | dados_powerbi.html | OK* | OK* | OK* | OK* | OK* | OK* | N/A** | OK | OK | N/A | R01 |
| 11 | Produtividade | `/produtividade` | produtividade.html | OK* | OK* | OK* | OK* | OK* | OK* | N/A** | OK | OK | N/A | R01 |
| 12 | Apresentação | `/apresentacao` | apresentacao.html | N/A | N/A | OK* | OK* | OK* | OK* | N/A | N/A | N/A | OK* | Desktop-first |
| 13 | Preview | `/preview` | preview.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | N/A | N/A | N/A | R01 stub |
| 14 | Análises | `/analises` | analises.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | N/A | N/A | N/A | R01 stub |
| 15 | Tendências | `/tendencias` | tendencias.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | N/A | N/A | N/A | R01 stub |
| 16 | Upload intelig. | `/upload_inteligente` | upload_inteligente.html | OK* | OK* | OK* | OK* | OK* | OK* | PARCIAL | N/A | OK | N/A | R01 parcial |
| 17 | Dash PowerBI | `/dashboard_powerbi` | dashboard_powerbi.html | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | N/A | N/A | N/A | PARCIAL | Pendente R06 |
| 18 | Auto processor | `/auto_processor` | auto_processor.html | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | NÃO TESTADO | N/A | N/A | OK | N/A | Pendente R06 |
| 19 | Download app | (sem rota) | download_app.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | N/A | N/A | N/A | R01 |
| 20 | INSS | (sem rota) | inss.html | OK* | OK* | OK* | OK* | OK* | OK* | OK | OK | OK | N/A | R01 |
| 21 | Baixar ícone | (sem rota) | baixar_icone.html | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | Utility |

\* Validação estática + smoke HTTP local; evidência visual browser quando disponível.  
\*\* Layout sem sidebar clássica do app (auth.js / shell próprio).

## Zoom

| Zoom | Dashboard | Login | Funcionários |
|------|-----------|-------|--------------|
| 100% | OK* | OK* | OK* |
| 125% | OK* | OK* | OK* |
| 150% | OK* | OK* | OK* |
