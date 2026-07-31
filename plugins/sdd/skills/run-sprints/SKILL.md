---
name: run-sprints
disable-model-invocation: true
description: >-
  Orquestra o método de sprints ponta a ponta, a partir de um de dois pontos de entrada: do zero
  (`spec` → `decompose` gera sprints de desenvolvimento) ou sobre um corpo de trabalho existente
  que precisa de correção (`review-quality` em escopo completo → achados aprovados pelo usuário →
  `decompose` gera sprints de correção). Dali em diante, por sprint: `execute-sprint` →
  `verify-sprint` como GATE → mini review, com checkpoint humano em cada fronteira e fechamento
  verificado. Fluxo de alto impacto e longa duração — roda apenas via "/run-sprints" explícito; as
  primitivas continuam auto-invocáveis avulsas para uso pontual. Agnóstica de domínio e tecnologia.
argument-hint: "[alvo ou objetivo]"
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.4.0"
---

# run-sprints

Orquestra as skills primitivas do método de sprints, a partir de um de dois pontos de entrada:

- **Do zero** — nada construído ainda: **spec → decompose** gera sprints de desenvolvimento.
- **Endurecimento** — código/repo já existe e precisa de correção: **review-quality (escopo
  completo) → achados aprovados → decompose** gera sprints de correção, um por achado.

A partir do decompose, o procedimento é **idêntico** nos dois casos: por sprint, **execute-sprint →
verify-sprint [GATE] → mini review**, checkpoint humano em cada fronteira, fechando com uma checagem
verificada. Não reimplementa nenhuma fase — sequencia, insere checkpoints, e **para no vermelho** em
vez de seguir sobre uma falha.

Genérica: não conhece linguagem, framework ou ferramenta. Comandos concretos vivem no `CLAUDE.md`
do projeto, responsabilidade das primitivas. Esta skill só decide qual etapa vem agora e se é
seguro avançar.

## Por que o disparo é manual

`disable-model-invocation: true` é deliberado: rodar o ciclo inteiro mexe em código, gera commits e
consome tempo — o início é decisão do usuário, nunca inferida de uma frase solta como "acho que vou
construir X".

## Qual entrada usar

- Requisitos ainda soltos ou nada construído → comece pela **spec**.
- Código já existe e a pergunta é "está certo?", "conserta isso", "audita e corrige" → comece pela
  **review-quality**.
- Ambíguo → pergunte antes de disparar a primeira fase; não presuma.

## Pré-condições

- Skills primitivas disponíveis: `spec`, `decompose`, `execute-sprint`, `verify-sprint`,
  `review-quality` (idealmente no mesmo plugin).
- Repositório/corpo de trabalho sob controle de versão — checkpoints commitam por sprint.

## Procedimento

Copie e mantenha atualizado ao longo do fluxo:

```
- [ ] 1. Entrada definida — spec fechada OU achados de review aprovados
- [ ] 2. Decompose gerou os sprints
- [ ] 3. Plano de sprints aprovado pelo usuário
- [ ] 4. Sprints executados (loop 4a-4d por sprint, até o total)
- [ ] 5. Fechamento verificado
```

**1. Entrada.**
- *Do zero:* invoque `spec`. Fase conversacional — pode levar várias trocas. **Checkpoint:** só
  avance quando o usuário considerar a especificação fechada, não pela sua própria avaliação.
- *Endurecimento:* invoque `review-quality` em escopo completo sobre o alvo indicado (pergunte o
  alvo se não foi dito) — ela roda em subagent próprio. Apresente os achados — **checkpoint
  humano**: o usuário confirma quais corrigir, reprioriza (a ordem do relatório é sugestão, não
  decreto) ou adia; só os aprovados seguem adiante. Se ela não achar nada relevante, o ciclo
  termina aqui: reporte
  "nada a corrigir" em vez de inventar correção para justificar o fluxo.

**2. Decompose.** Invoque `decompose` sobre a spec fechada ou os achados aprovados. Produz sprints
com ordem justificada, dependências explícitas e entregável verificável por sprint — no
endurecimento, um sprint de correção por achado (checkpoint limpo, rollback fácil; amontoar achados
embaralha a prova de qual correção quebrou o quê), e o entregável prova que aquele bug específico
sumiu.

**3. Aprovação do plano.** Apresente o plano de sprints e espere aprovação do usuário antes de
executar qualquer coisa — último ponto barato para corrigir rumo. Não pule para "ganhar tempo".

**4. Loop de execução** — por sprint, nesta ordem (conformidade antes de qualidade):

  a. **`execute-sprint`** no próximo sprint: planeja, implementa só aquele escopo, valida, commita.
     A aprovação do plano no passo 3 cobre o plano de cada sprint — o executor não para para
     reaprovar; só volta ao usuário se surgir decisão de design que o plano aprovado não cobre.

  b. **`verify-sprint`** (subagent independente) — GATE de conformidade: o entregue corresponde ao
     que o sprint definiu? Escopo cumprido, restrições respeitadas, entregável comprovado.
     - CONFORME → segue para 4c.
     - NÃO CONFORME / PARCIAL → **pare e reporte**. Não feche o sprint, não vá ao mini review.

     Roda antes do mini review porque um sprint pode estar bem-feito e ainda assim fora do escopo —
     checar aderência primeiro evita gastar revisão de qualidade em algo já descartado.

  c. **`review-quality`** em escopo pequeno — só o diff do sprint. No endurecimento, confirma duas coisas:
     o bug de fato sumiu, **e** nada foi quebrado em volta (o coração do endurecimento: corrigir A e
     quebrar B silenciosamente é retrocesso, não progresso). Do zero, checa qualidade (bugs, lógica,
     contrato × comportamento).

  d. **Checkpoint.** Falha em qualquer etapa (a/b/c), inclusive regressão detectada → pare e
     reporte, não avance automaticamente. Sucesso → próximo sprint, preferencialmente com contexto
     limpo (o sprint seguinte usa seu prompt e o estado commitado, não a memória da conversa
     anterior).

**5. Fechamento verificado.** Não declare "pronto"/"resolvido" por sensação. Confirme com prova:
- estado do repositório (tudo commitado, nada pela metade);
- checagens do projeto (`CLAUDE.md`/regras);
- *do zero:* `review-quality` final em escopo completo — inconsistências entre camadas, integração entre
  sprints, o todo contra o contrato original — o que os mini reviews locais não veem; achados dela
  **não são corrigidos aqui**, encaminhe para um novo `/run-sprints` (entrada endurecimento);
- *endurecimento:* cada achado endereçado, com a prova por sprint **re-executada do estado limpo** —
  não só relatada como verde;
- smoke do caminho flagship: rode, a partir de estado limpo, o comando de dia-zero (install/start/
  deploy, ou o fluxo que as correções tocam) — a integração de ponta a ponta que nenhum gate
  por-sprint enxerga.

Prova está no artefato, não na nota: se algo que a entrega precisa só existe como promessa e não
está no repositório, não está pronto. Fechamento honesto: "sprints entregues e verificados; review
final apontou X achados, encaminhados para novo ciclo" ou "achados A, B, C corrigidos e verificados;
D, E ficaram para fases futuras a pedido do usuário" — não "acho que está tudo certo".

## Formato de saída

Ao reportar progresso, parar ou fechar, use o painel em
[`assets/painel-orquestracao.md`](assets/painel-orquestracao.md), mantendo exatamente a estrutura
dele. Ao parar, deixe claro **qual
sprint**, **qual etapa** (execução/gate/mini review) e **por quê** — "parou e reportou com motivo
concreto" é resultado válido, não fracasso.

## Fronteiras

- Não implementa sprints (`execute-sprint` faz isso) nem audita (`review-quality` faz isso).
- Não especifica, decompõe ou revisa por conta própria — só encadeia as primitivas.
- Não corrige achados fora do ciclo aprovado — achados adiados ficam de fora, não viram sprint por
  conta própria.
- Não é auto-invocável — só roda com `/run-sprints` explícito. As primitivas continuam
  auto-invocáveis para uso pontual (ex.: uma `review-quality` avulsa, sem o ciclo completo).
