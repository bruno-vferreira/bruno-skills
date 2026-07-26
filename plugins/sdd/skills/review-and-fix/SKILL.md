---
name: review-and-fix
disable-model-invocation: true
description: >-
  Orquestra o ciclo de REVISAR e CORRIGIR um corpo de trabalho que já existe: audita o código
  (`review` em escopo completo), transforma os achados aprovados em sprints de correção — um por
  achado (`decompose`) — e executa cada correção com verificação (`execute-sprint` → `verify-sprint`
  como GATE → mini review do diff), fechando com uma checagem verificada de que os bugs sumiram e
  nada quebrou em volta. É o fluxo de ENDURECIMENTO do que já existe, não de construção do zero
  (isso é `build-project`). Orquestra as primitivas, não as reimplementa. Fluxo de ALTO IMPACTO que
  altera código e tem longa duração — por isso é MANUAL: só roda quando o usuário a invoca
  explicitamente com `/review-and-fix`; o modelo NUNCA a dispara sozinho ao interpretar uma conversa
  ou um pedido de "dá uma revisada". A primitiva `review` sozinha continua auto-invocável para uma
  auditoria pontual; é o ciclo COMPLETO com correções que é deliberado. Aplica-se a qualquer domínio.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.2.0"
---

# review-and-fix

Conduz o ciclo **revisar → corrigir** de um corpo de trabalho que já existe: audita o repositório
(ou uma área dele), transforma os achados em **sprints de correção** e executa cada correção com
verificação, fechando com uma nova checagem. Fluxo macro do **endurecimento** — aplicado ao que já
foi construído e precisa ficar mais robusto, não ao que está sendo erguido do zero.

Orquestra, não reimplementa: cada fase é chamada à primitiva correspondente (`review`, `decompose`,
`execute-sprint`, `verify-sprint`). O valor está em sequenciar com rigor, inserir os pontos de
controle humano nos lugares certos, e **parar no vermelho** em vez de seguir sobre uma correção que
não fechou.

Genérica: comandos concretos (validar, commitar, provar que um bug sumiu) vivem no `CLAUDE.md` do
projeto e são responsabilidade das primitivas — esta skill só decide qual etapa vem agora e se é
seguro avançar.

## Por que o disparo é manual

`disable-model-invocation: true` é deliberado: um ciclo completo de revisão-e-correção mexe em
código, cria commits, consome tempo — o início é decisão do usuário, nunca inferida de "esse módulo
tá meio frágil" ou "dá uma olhada nesse código aí". A primitiva `review` continua auto-invocável
para auditoria pontual; é o ciclo completo com correções que exige `/review-and-fix` explícito.

## Pré-condições

- Skills primitivas disponíveis: `review`, `decompose`, `execute-sprint`, `verify-sprint`
  (idealmente no mesmo plugin).
- Corpo de trabalho existente sob controle de versão — checkpoints commitam por correção.

Se `/review-and-fix` foi chamado sem indicar o alvo, pergunte o que revisar (repo inteiro ou área
específica) antes de disparar a primeira fase — não presuma o escopo.

## Procedimento

Copie e mantenha atualizado ao longo do fluxo:

```
- [ ] 1. Review completa feita, achados levantados
- [ ] 2. Achados apresentados e aprovados pelo usuário
- [ ] 3. Decompose gerou um sprint de correção por achado aprovado
- [ ] 4. Plano de correções aprovado pelo usuário
- [ ] 5. Correções executadas (loop 5a-5d por sprint, até o total)
- [ ] 6. Fechamento verificado (prova por sprint + repo + checagens + nada regrediu)
```

**1. Revisar.** Invoque `review` em escopo completo sobre o alvo indicado, preferencialmente em
subagent, para produzir o relatório de achados priorizados. Fase de diagnóstico — não se corrige
nada aqui. Se a `review` não achar nada relevante, o ciclo termina: reporte "nada a corrigir" em vez
de inventar correções para justificar o fluxo.

**2. Apresentar os achados — checkpoint humano.** O relatório é ponto de decisão humana, não lista
de ordens automáticas. Apresente e espere confirmação de quais corrigir: o usuário confirma,
reprioriza (a ordem da `review` é sugestão, não decreto), ou adia achados para fases futuras. Só os
**aprovados** seguem para a decomposição — corrigir tudo sem passar pelo usuário atropela o controle
humano que esta fase existe para garantir.

**3. Decompor.** Invoque `decompose` sobre os achados aprovados — **um sprint de correção por
achado**. A decomposição ordena por severidade + dependências + vitória rápida, e dá a cada um o
entregável verificável: a prova de que aquele bug específico sumiu. Um achado, um sprint é
deliberado — checkpoint limpo, rollback fácil; amontoar achados embaralha a prova (qual correção
quebrou o quê?).

**4. Aprovação do plano.** Apresente o plano de correções e espere aprovação antes de executar
qualquer coisa — último ponto barato para corrigir rumo.

**5. Loop de correção** — por sprint, nesta ordem (conformidade antes de qualidade):

  a. **`execute-sprint`** na próxima correção: planeja, implementa só aquele escopo, valida a prova
     de que o bug sumiu, commita.

  b. **`verify-sprint`** (subagent independente) — GATE: a correção corresponde ao definido,
     inclusive a prova exigida ("bug X sumiu") foi produzida e testa a coisa certa, não uma prova
     adjacente?
     - CONFORME → segue para 5c.
     - NÃO CONFORME / PARCIAL → **pare e reporte**. Não feche a correção, não vá ao mini review.

     Antes do mini review porque uma correção pode estar bem-feita e ainda não provar que o bug
     sumiu — checar aderência primeiro evita gastar revisão de qualidade em algo já fora do
     combinado.

  c. **`review`** em escopo pequeno — só o diff da correção, confirmando duas coisas: (a) o bug de
     fato sumiu, (b) nada foi quebrado em volta. O item (b) é o coração do endurecimento: corrigir A
     e quebrar B silenciosamente é retrocesso, não progresso.

  d. **Checkpoint.** Falha em execução, gate, ou mini review — inclusive regressão detectada —
     → pare e reporte, não avance automaticamente. Sucesso → próxima correção, preferencialmente com
     contexto limpo.

**6. Fechamento verificado.** Não declare "resolvido" por sensação. Confirme com prova:
- cada achado endereçado foi de fato corrigido — a prova por sprint foi produzida e **re-executada
  do estado limpo**, não só relatada como verde;
- estado do repositório (correções commitadas, nada pela metade);
- checagens do projeto (`CLAUDE.md`/regras);
- nada em volta regrediu — smoke do fluxo que as correções tocam, de ponta a ponta.

Prova está no artefato, não na nota: um achado só está fechado quando a correção está no código
entregue e a prova foi re-executada — não quando um commit *diz* que corrigiu.

Fechamento honesto: "achados A, B, C corrigidos e verificados; D, E ficaram para fases futuras a
pedido do usuário" — não "acho que tá tudo resolvido". Se a correção fizer novas questões surgirem,
elas originam outro ciclo de `/review-and-fix`, não algo emendado silenciosamente aqui.

## Formato de saída

Ao reportar progresso, parar ou fechar, use o painel em
[`assets/painel-orquestracao.md`](assets/painel-orquestracao.md). Ao parar, deixe claro **qual
correção**, **qual etapa** e **por quê** — "parou e reportou" com motivo concreto (ex.: "a correção
do achado 3 passou o gate mas o mini review detectou que quebrou o parsing adjacente") é resultado
válido, não fracasso.

## Princípios (quando o roteiro não cobrir o caso)

- Orquestrar, não reimplementar — se estiver auditando, decompondo ou corrigindo à mão aqui, saiu
  do papel: delegue.
- Um achado, um sprint — correções isoladas para checkpoint limpo e rollback fácil.
- Prova por correção — sem evidência de que o bug sumiu e nada quebrou em volta, não é correção
  fechada, é esperança.
- Achados e plano de correção são aprovados pelo usuário antes de executar; adiar um achado é
  decisão dele, não sua.
- Falha para o fluxo, sucesso avança. Gate antes do mini review; parada no vermelho inclusive por
  regressão.
- Fechamento é verificado, não sentido.

## Fronteiras

- Não constrói do zero — isso é `build-project`. Esta skill endurece o que já existe.
- Não reimplementa `review`, `decompose` ou a execução — só as encadeia.
- Não corrige achados que o usuário adiou — ficam de fora do ciclo atual, não viram sprint por
  conta própria.
- Não é auto-invocável — só roda com `/review-and-fix` explícito. A `review` sozinha pode ser
  disparada pelo modelo para auditoria pontual.

## Variantes por tecnologia

Agnóstica por decisão: a sequência de fases e os checkpoints não mudam entre domínios; comandos
concretos vivem nas primitivas e no `CLAUDE.md` do projeto. Se surgir necessidade de guia
específico, entra como `references/<tema>.md`, lido sob demanda.
