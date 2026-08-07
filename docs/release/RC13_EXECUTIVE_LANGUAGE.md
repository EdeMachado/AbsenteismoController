# RC-1.3 — Executive Language & Trust

**Branch:** `cursor/rc13-executive-language-trust-f8f5`
**HEAD:** `bc7407ba31920bdd9813a6fa1321ac5855760f62`
**Status:** Draft · sem merge · sem deploy · sem produção

## Pergunta da sprint

O sistema transmite confiança?

## Critérios

- Uma só voz: institucional, executiva, humana, objetiva
- Sem jargão técnico na interface
- IA sugestiva: “A análise sugere” / “As evidências apontam” / “Necessária validação”
- Erros que transmitem segurança
- Botões padronizados
- Sem marketing exagerado

## Fora de escopo

Sem novas funcionalidades · sem mudança de regra de negócio · sem Analytics/IA/banco/API estrutural · sem telas novas · sem merge/deploy/produção.

## Antes → Depois (exemplos)

| Antes | Depois |
|-------|--------|
| Dataset / sintético | Base / Demonstração |
| MetricService, rule engine, LLM | Métricas agregadas, priorização determinística, necessária validação |
| engine=rule_engine | (removido da UI) |
| neste payload | neste período |
| Error state | Estado de erro |
| Token opaco / Reset demo | Acesso individual / Reiniciar demonstração |
| Enviar ficha | Solicitar preenchimento |
| Evidence Summary / Business Impact | Síntese da evidência / Impacto para o negócio |
| Decision Experience (chrome) | Decisão |
| Falha / Command Center / ENABLE_* | Não foi possível concluir esta ação… |
| Sugere revisão… | A análise sugere revisão… — necessária validação |

## Decisões de linguagem

1. **Questionário** no lugar de “ficha” nas superfícies humanas (status internos do fluxo permanecem).
2. Títulos executivos em português; nomes de produto em inglês removidos do chrome.
3. Metodologia exibida com rótulos humanos; mapeamento cobre rótulos técnicos legados.
4. Confirmações curtas: “Informações recebidas”, “Análise validada”.
5. Botões: Continuar, Voltar, Entender esta decisão, Como sabemos disso?, Solicitar preenchimento, Validar análise, Concluir, Cancelar/Reiniciar demonstração.

## Screenshots

`tests/artifacts/rc13_language/before/` e `after/`

## Testes

`tests/release/test_rc13_executive_language.py`

## Confirmação

Sem merge · sem deploy · sem produção. Não inicia RC-1.4.
