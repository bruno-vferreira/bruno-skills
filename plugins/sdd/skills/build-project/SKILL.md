---
name: build-project
disable-model-invocation: true
description: >-
  Orquestra a construção de um projeto do zero ao fim, encadeando as etapas do método de sprints:
  especificar os requisitos (`spec`), decompor em sprints (`decompose`), executar cada sprint com
  verificação (`execute-sprint` → `verify-sprint` como GATE → mini review) e, ao final, revisar o
  repositório inteiro (`review`). É o fluxo macro que transforma "quero construir X" em um projeto
  implementado, verificado e revisado, com checkpoint em cada fronteira. Fluxo de ALTO IMPACTO e
  longa duração — por isso é MANUAL: só roda quando o usuário a invoca explicitamente com
  `/build-project`; o modelo NUNCA a dispara sozinho ao interpretar uma conversa. Orquestra as
  primitivas, não as reimplementa. Não corrige achados de review (isso é o fluxo `review-and-fix`).
  Aplica-se a qualquer domínio.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.1.0"
---

# build-project

Esta skill conduz um projeto **do zero ao fim** encadeando as skills primitivas do método de
sprints na ordem certa: **entender** os requisitos → **especificar** → **decompor** em sprints →
**executar** cada sprint com verificação → **revisar**. É o fluxo de **orquestração** que
transforma "quero construir X" em um projeto implementado, verificado e revisado — mantendo a
disciplina de **checkpoint em cada fronteira**.

Ela **orquestra, não reimplementa**: cada fase é uma **chamada à primitiva correspondente**
(`spec`, `decompose`, `execute-sprint`, `verify-sprint`, `review`). O valor desta skill não está em
fazer o trabalho de nenhuma etapa, e sim em **sequenciá-las com rigor**, inserir os **pontos de
controle humano** nos lugares certos e **parar no vermelho** em vez de seguir por cima de uma falha.

É **genérica**: não conhece linguagens, frameworks ou ferramentas. Os comandos concretos (como
validar, como commitar) vivem no `CLAUDE.md` do projeto e são responsabilidade das primitivas — esta
skill só decide **qual etapa vem agora** e **se é seguro avançar**.

## Por que o disparo é manual (decisão de arquitetura)

Esta skill tem **`disable-model-invocation: true`** no frontmatter: ela **só** roda quando o usuário
a chama explicitamente com `/build-project`. Isso é deliberado.

Iniciar a construção de um projeto inteiro é uma ação de **alto impacto e longa duração** — mexe em
código, cria commits, gasta tempo e contexto. O **controle do início é do usuário**, não uma decisão
que o modelo deva tomar sozinho ao interpretar uma frase como "acho que vou construir um X". As
**primitivas** continuam auto-invocáveis (o modelo pode `spec`-ar ou `review`-ar sob demanda); é a
**orquestração completa** que é deliberada. Se você é o modelo e está lendo isto fora de um
`/build-project` explícito, **não inicie o fluxo** — no máximo, sugira que o usuário rode
`/build-project` quando quiser conduzir o projeto inteiro.

## Pré-condições

Antes de orquestrar, confirme que existe:

- **As skills primitivas disponíveis** — `spec`, `decompose`, `execute-sprint`, `verify-sprint` e
  `review`. Esta skill as chama; se alguma faltar, a fase correspondente não tem como rodar. (O
  ideal é que estejam empacotadas juntas no mesmo **plugin**.)
- **Um repositório sob controle de versão** — os checkpoints **commitam por sprint**. Sem versão,
  não há como isolar um sprint nem voltar atrás quando um gate reprova.

Se o usuário chamou `/build-project` mas ainda não há requisito nenhum, tudo bem: a primeira fase
(`spec`) existe justamente para **capturar** os requisitos em conversa. Comece por ela.

## Procedimento (a orquestração)

Siga as fases em ordem. Cada uma é uma **chamada à primitiva**, com o seu "porquê" para você julgar
bem quando o caso real fugir do roteiro. O princípio que atravessa tudo: **falha para o fluxo;
sucesso avança**.

### 1. Especificar — invocar `spec`

Invoque a `spec` para transformar os requisitos brutos do usuário em uma **especificação rigorosa**.
Essa fase é **conversacional** e pode levar várias trocas: a `spec` anota, confirma, caça lacunas e
consolida o contrato do que será construído.

**Ponto de controle humano:** só avance para a decomposição quando o **usuário considerar a
especificação fechada**. Fechar cedo é herdar suposições que ninguém validou — a decomposição
seguinte carregaria os buracos adiante. Não declare a spec "pronta" pela sua sensação; espere o sinal
do usuário.

### 2. Decompor — invocar `decompose`

Com a especificação fechada, invoque a `decompose` sobre ela para gerar os **sprints**: unidades de
escopo fechado, com **ordem justificada**, **dependências explícitas** e, cada uma, um **entregável
verificável**. O produto é o **índice da sequência** mais um **prompt por sprint**, prontos para a
`execute-sprint`.

### 3. Confirmar o plano com o usuário

Antes de executar qualquer coisa, **apresente o plano de sprints ao usuário e espere aprovação**. A
decomposição é um **ponto de revisão humana**: o usuário aprova, reordena ou ajusta o escopo. Este é
o último momento barato para corrigir o rumo — depois daqui começa a mexer em código. Não pule este
checkpoint "para ganhar tempo"; ele é o que evita construir a coisa errada com eficiência.

### 4. Loop de execução — um sprint por vez

Para cada sprint, na ordem do plano, execute **este ciclo completo** antes de olhar o próximo. A
ordem interna importa: **conformidade antes de qualidade**.

1. **Executar — `execute-sprint`.** Invoque a `execute-sprint` para o próximo sprint. Ela planeja,
   implementa **apenas o escopo daquele sprint**, valida o entregável e commita.

2. **Gate de conformidade — `verify-sprint` (subagent independente).** Invoque a `verify-sprint`
   para julgar, **independente do executor**, se o que foi entregue corresponde ao que o sprint
   **definiu** — escopo cumprido, restrições respeitadas (nada de escopo futuro antecipado), e o
   entregável de fato comprovado. É um **GATE**:
   - **CONFORME** → libera a etapa seguinte.
   - **NÃO CONFORME** ou **PARCIAL** → **pare e reporte**. Não avance, não feche o sprint, não siga
     para o mini review. O gate reprovar é sinal de que a entrega desviou do combinado; seguir por
     cima disso propaga o desvio.

   Por que **antes** do mini review: um sprint pode estar bem-feito e ainda assim **não
   corresponder** ao que foi pedido. Verificar aderência primeiro evita gastar uma revisão de
   qualidade em algo que já está fora do escopo.

3. **Mini review — `review` em escopo pequeno.** Passado o gate, invoque a `review` sobre **apenas o
   diff daquele sprint** (não o repo inteiro) para uma checagem de **qualidade** — bugs, lógica,
   contrato × comportamento — no que acabou de ser feito.

4. **Checkpoint.** Se a **execução**, o **gate** ou o **mini review** revelarem falha, **pare e
   reporte** ao usuário; **não avance automaticamente** para o próximo sprint. Se tudo passou, siga
   para o próximo sprint — idealmente com **contexto limpo** entre sprints (o que um sprint precisa
   saber está no seu prompt e no estado commitado, não na memória de conversa do anterior).

### 5. Revisão final — invocar `review` em escopo completo

Concluídos **todos** os sprints, invoque a `review` sobre o **repositório inteiro** para uma
**auditoria final** — a visão que os mini reviews, por serem locais, não enxergam: inconsistências
entre camadas, integração entre os sprints, o todo contra o contrato original.

### 6. Fechamento verificado

**Não declare o projeto "pronto" pela sensação.** Confirme, com prova:

- o **estado do repositório** (todos os sprints commitados, nada pela metade),
- as **checagens do projeto** (o que o `CLAUDE.md`/regras exigem),
- o **resultado da revisão final**,
- um **smoke do caminho flagship** — rode, **a partir de um estado limpo**, o **comando de dia-zero**
  que um usuário/operador usaria para pôr o sistema no ar de ponta a ponta (o `install`/`start`/
  `deploy`). Cada sprint prova a **sua** fatia; o **todo** — a integração que faz o sistema funcionar
  de fato pela porta da frente — nenhum gate por-sprint enxerga. É o que a revisão final e este smoke
  pegam.

E **prova está no artefato, não na nota**: "todos os sprints verdes" ou "o item X foi resolvido" não é
fechamento — se algo que a entrega precisa (o orquestrador de bootstrap, um pin revertido, um doc
alinhado ao código) só existe como promessa e **não está no repositório entregue**, o projeto **não
está pronto**. Cuidado com o momentum do "quase tudo verde, pode entregar": um bloqueador de release
não some porque os sprints passaram.

Se a revisão final **gerar achados**, **não os corrija aqui** — encaminhe-os para o fluxo de
correção (`/review-and-fix`, que decompõe os achados em sprints de correção e os executa com o mesmo
rigor). O fechamento honesto é: "todos os sprints entregues e verificados; a revisão final apontou X
achados, encaminhados para correção" — não um "acho que está pronto".

## Formato de saída (painel de orquestração)

Conduza o fluxo mantendo o usuário orientado sobre **onde está** e **o que passou**. Ao reportar
progresso — e obrigatoriamente ao **parar** ou **fechar** —, use um painel como o de
[`assets/painel-orquestracao.md`](assets/painel-orquestracao.md):

```
# build-project — <projeto>
**Fase atual:** <spec | decompose | execução sprint N/total | review final | fechado>

## Sprints
| # | Sprint            | Execução | Gate (verify) | Mini review | Estado    |
|---|-------------------|----------|---------------|-------------|-----------|
| 1 | <nome>            | ✅        | ✅ CONFORME    | ✅           | fechado   |
| 2 | <nome>            | ✅        | ❌ NÃO CONFORME| —           | PAROU AQUI |
| 3 | <nome>            | —        | —             | —           | pendente  |

## Checkpoints humanos
- [x] Especificação fechada pelo usuário
- [x] Plano de sprints aprovado pelo usuário

## Situação
<CONFORME e seguindo | PAROU no sprint N — motivo + o que reportar | FECHADO — resultado da review final>
```

Quando o fluxo **para** num vermelho, o painel deve deixar claro **em qual sprint**, **em qual
etapa** (execução/gate/mini review) e **por quê** — para o usuário decidir o próximo passo. Um
"parou e reportou" com o motivo concreto é um resultado **válido**, não um fracasso.

## Princípios (o núcleo, quando o roteiro não cobrir o caso)

- **Orquestrar, não reimplementar.** Cada fase é uma chamada à primitiva. Se você se pegar
  escrevendo código de spec, de decomposição ou de execução aqui dentro, saiu do papel: delegue.
- **Pontos de controle humano.** A **especificação** e o **plano de sprints** são aprovados pelo
  usuário antes de executar. O início do fluxo também é do usuário (disparo manual).
- **Checkpoint em cada fronteira.** Falha **para** o fluxo; sucesso **avança**. Gate de conformidade
  **antes** do mini review; mini review entre sprints; review completo no fim.
- **Conformidade antes de qualidade.** `verify-sprint` (fez o que prometeu?) roda **antes** da
  `review` (está bem-feito?) — porque um trabalho bem-feito ainda pode estar fora do escopo.
- **Fechamento é verificado, não sentido.** "Pronto" exige prova: repo, checagens e revisão final —
  não uma impressão.
- **Manual e deliberada.** Esta skill nunca é auto-invocada; o usuário decide o início.

## Fronteiras (o que esta skill NÃO faz)

- **Não implementa sprints** — delega à `execute-sprint`. Aqui não se escreve o código de um sprint.
- **Não especifica, decompõe nem revisa por conta própria** — cada uma dessas é a sua primitiva
  (`spec`, `decompose`, `review`). Esta skill só as **encadeia**.
- **Não corrige achados de review** — isso é o fluxo de orquestração irmão, `review-and-fix`. A
  `build-project` **constrói do zero**; endurecer o que já existe via revisar-e-corrigir é o outro
  fluxo. Ao fim, os achados da revisão final são **encaminhados** para lá, não resolvidos aqui.
- **Não é auto-invocável** — só roda com `/build-project` explícito.

## Variantes por tecnologia (futuro)

A orquestração é agnóstica de tecnologia por decisão: a **sequência** de fases e os **checkpoints**
não mudam entre um projeto de dados, uma API ou uma migração — o que muda são os comandos concretos,
que vivem nas primitivas e no `CLAUDE.md` do projeto. Não há variantes de stack previstas para esta
camada. Se algum dia surgir necessidade de um guia específico, ele entra como `references/<tema>.md`,
lido sob demanda — o núcleo (encadear com checkpoints) permanece genérico.
