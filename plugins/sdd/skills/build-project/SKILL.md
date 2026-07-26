---
name: build-project
disable-model-invocation: true
description: >-
  Orquestra a construção de um projeto do zero ao fim, encadeando as etapas do método de sprints:
  especificar (`spec`), decompor (`decompose`), executar cada sprint com verificação
  (`execute-sprint` → `verify-sprint` como GATE → mini review) e revisar o repositório inteiro ao
  final (`review`). Transforma "quero construir X" em um projeto implementado, verificado e
  revisado, com checkpoint em cada fronteira. Fluxo de ALTO IMPACTO e longa duração — MANUAL: só
  roda com `/build-project` explícito, o modelo NUNCA a dispara sozinho. Orquestra as primitivas,
  não as reimplementa. Não corrige achados de review (isso é `review-and-fix`). Agnóstica de
  domínio e tecnologia.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.2.0"
---

# build-project

Orquestra as skills primitivas do método de sprints, em ordem: **spec → decompose → (execute-sprint
→ verify-sprint [GATE] → mini review) por sprint → review final**. Não reimplementa nenhuma fase —
sequencia, insere checkpoints humanos, e **para no vermelho** em vez de seguir sobre uma falha.

Genérica: não conhece linguagem, framework ou ferramenta. Comandos concretos vivem no `CLAUDE.md`
do projeto, responsabilidade das primitivas. Esta skill só decide qual etapa vem agora e se é
seguro avançar.

## Por que o disparo é manual

`disable-model-invocation: true` é deliberado: iniciar um projeto inteiro mexe em código, gera
commits, consome tempo — o início é decisão do usuário, nunca inferida de uma frase como "acho que
vou construir X". As primitivas continuam auto-invocáveis avulsas; é a orquestração completa que
exige `/build-project` explícito.

## Pré-condições

- Skills primitivas disponíveis: `spec`, `decompose`, `execute-sprint`, `verify-sprint`, `review`
  (idealmente no mesmo plugin).
- Repositório sob controle de versão — checkpoints commitam por sprint.

Se `/build-project` foi chamado sem requisitos ainda definidos, comece pela fase 1 (`spec` existe
para capturá-los).

## Procedimento

Copie e mantenha atualizado ao longo do fluxo:

```
- [ ] 1. Spec fechada pelo usuário
- [ ] 2. Decompose gerou sprints
- [ ] 3. Plano de sprints aprovado pelo usuário
- [ ] 4. Sprints executados (loop 4a-4d por sprint, até o total)
- [ ] 5. Review final feita
- [ ] 6. Fechamento verificado (repo + checagens + review + smoke)
```

**1. Spec.** Invoque `spec`. Fase conversacional — pode levar várias trocas. **Checkpoint:** só
avance quando o usuário considerar a especificação fechada, não pela sua própria avaliação.

**2. Decompose.** Invoque `decompose` sobre a spec fechada. Produz sprints com ordem justificada,
dependências explícitas e entregável verificável por sprint.

**3. Aprovação do plano.** Apresente o plano de sprints e espere aprovação do usuário antes de
executar qualquer coisa — último ponto barato para corrigir rumo. Não pule para "ganhar tempo".

**4. Loop de execução** — por sprint, nesta ordem (conformidade antes de qualidade):

  a. **`execute-sprint`** no próximo sprint: planeja, implementa só aquele escopo, valida, commita.

  b. **`verify-sprint`** (subagent independente) — GATE de conformidade: o entregue corresponde ao
     que o sprint definiu? Escopo cumprido, restrições respeitadas, entregável comprovado.
     - CONFORME → segue para 4c.
     - NÃO CONFORME / PARCIAL → **pare e reporte**. Não feche o sprint, não vá ao mini review.

     Roda antes do mini review porque um sprint pode estar bem-feito e ainda assim fora do escopo —
     checar aderência primeiro evita gastar revisão de qualidade em algo já descartado.

  c. **`review`** em escopo pequeno — só o diff do sprint, checando qualidade (bugs, lógica,
     contrato × comportamento).

  d. **Checkpoint.** Falha em qualquer etapa (a/b/c) → pare e reporte, não avance automaticamente.
     Sucesso → próximo sprint, preferencialmente com contexto limpo (o sprint seguinte usa seu
     prompt e o estado commitado, não a memória da conversa anterior).

**5. Review final.** Todos os sprints concluídos → invoque `review` no repositório inteiro:
inconsistências entre camadas, integração entre sprints, o todo contra o contrato original — o que
os mini reviews locais não veem.

**6. Fechamento verificado.** Não declare "pronto" por sensação. Confirme com prova:
- estado do repositório (tudo commitado, nada pela metade);
- checagens do projeto (`CLAUDE.md`/regras);
- resultado da review final;
- smoke do caminho flagship: rode, a partir de estado limpo, o comando de dia-zero
  (install/start/deploy) que um operador usaria — é a integração de ponta a ponta que nenhum gate
  por-sprint enxerga.

Prova está no artefato, não na nota: se algo que a entrega precisa só existe como promessa e não
está no repositório, o projeto não está pronto. "Quase tudo verde" não elimina um bloqueador real.

Achados da review final **não são corrigidos aqui** — encaminhe para `/review-and-fix`. Fechamento
honesto: "sprints entregues e verificados; review final apontou X achados, encaminhados para
correção", não "acho que está pronto".

## Formato de saída

Ao reportar progresso, parar ou fechar, use o painel em
[`assets/painel-orquestracao.md`](assets/painel-orquestracao.md). Ao parar, deixe claro **qual
sprint**, **qual etapa** (execução/gate/mini review) e **por quê** — "parou e reportou com motivo
concreto" é resultado válido, não fracasso.

## Princípios (quando o roteiro não cobrir o caso)

- Orquestrar, não reimplementar — se estiver escrevendo código de spec/decomposição/execução aqui,
  delegue.
- Especificação e plano de sprints são aprovados pelo usuário antes de executar; início do fluxo
  também é dele.
- Falha para o fluxo, sucesso avança. Gate antes do mini review; mini review por sprint; review
  completa no fim.
- Fechamento é verificado, não sentido.

## Fronteiras

- Não implementa sprints (`execute-sprint` faz isso).
- Não especifica, decompõe ou revisa por conta própria — só encadeia as primitivas.
- Não corrige achados de review — encaminha para `review-and-fix`.
- Não é auto-invocável — só roda com `/build-project` explícito.

## Variantes por tecnologia

Agnóstica por decisão: a sequência de fases e checkpoints não muda entre domínios; comandos
concretos vivem nas primitivas e no `CLAUDE.md` do projeto. Se surgir necessidade de guia
específico de stack, entra como `references/<tema>.md`, lido sob demanda.
