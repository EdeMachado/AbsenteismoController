# Comparabilidade de Janelas

## Equivalências (fonte mensal)

| Janela nominada | Competências |
|-----------------|--------------|
| 30 dias | 1 |
| 60 dias | 2 |
| 90 dias | 3 |
| 180 dias | 6 |
| 12 meses | 12 |

**Aviso:** dado mensal **não** equivale a precisão diária. O resolvedor não finge granularidade diária.

Também suportados:

- mesmo período do ano anterior (−12 competências);
- trimestre civil equivalente;
- semestre civil equivalente.

## Checagens antes da análise integral

- mesma quantidade de meses;
- meses completos (uploads em todas as competências esperadas);
- competências contíguas;
- metodologia de horas equivalente;
- cobertura de horas comparável (Δ ≤ limiar);
- presença de dados;
- períodos não sobrepostos (antes/depois).

## Modos

| Modo | Significado |
|------|-------------|
| `integral` | janelas comparáveis — classificação de eficácia permitida |
| `descritiva` | divergências suaves — só leitura descritiva |
| `bloqueada` | falhas duras — sem eficácia integral |

Associação temporal **não** comprova causalidade.
