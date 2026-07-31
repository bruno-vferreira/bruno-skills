# run-sprints — <projeto/alvo>
**Entrada:** <do zero (spec) | endurecimento (review)>
**Fase atual:** <spec | review | decompose | execução sprint N/total | fechamento>

## Sprints
| # | Sprint / achado | Execução | Gate (verify) | Mini review | Estado |
|---|------------------|----------|----------------|--------------|--------|
| 1 |                  | ✅ / ❌ / — | ✅ CONFORME / ⚠️ PARCIAL / ❌ NÃO CONFORME / — | ✅ / ❌ / — | fechado / PAROU AQUI / pendente |

*(entrada "do zero": coluna é o sprint. Entrada "endurecimento": coluna é o achado que originou o
sprint de correção, e o mini review confirma "bug sumiu, nada quebrou".)*

## Checkpoints
- [ ] Entrada fechada — spec aprovada pelo usuário, ou achados de review aprovados
- [ ] Plano de sprints aprovado pelo usuário

## Status
<CONFORME e seguindo | PAROU no sprint/achado N, etapa <execução/gate/mini review> — motivo + o que
reportar | FECHADO (do zero) — resultado da review final, achados encaminhados a novo /run-sprints
se houver | FECHADO (endurecimento) — achados corrigidos e verificados com prova re-executada;
adiados listados; novas questões encaminhadas a outro ciclo>
