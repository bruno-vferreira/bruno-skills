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
---

# review-and-fix

Esta skill conduz o ciclo **revisar → corrigir** de um corpo de trabalho **que já existe**: audita o
repositório (ou uma área dele), transforma os achados em **sprints de correção** e executa cada
correção com verificação, fechando com uma nova checagem. É o **fluxo macro do endurecimento** —
aplicado a algo que já foi construído e precisa ficar mais robusto, em vez de erguido do zero.

Ela **orquestra, não reimplementa**: cada fase é uma **chamada à primitiva correspondente**
(`review`, `decompose`, `execute-sprint`, `verify-sprint`). O valor desta skill não está em fazer o
trabalho de nenhuma etapa, e sim em **sequenciá-las com rigor**, inserir os **pontos de controle
humano** nos lugares certos e **parar no vermelho** em vez de seguir por cima de uma correção que
não fechou.

É **genérica**: não conhece linguagens, frameworks ou ferramentas. Os comandos concretos (como
validar, como commitar, como provar que um bug sumiu) vivem no `CLAUDE.md` do projeto e são
responsabilidade das primitivas — esta skill só decide **qual etapa vem agora** e **se é seguro
avançar**.

## Por que o disparo é manual (decisão de arquitetura)

Esta skill tem **`disable-model-invocation: true`** no frontmatter: ela **só** roda quando o usuário
a chama explicitamente com `/review-and-fix`. Isso é deliberado.

Iniciar um ciclo completo de revisão-e-correção é uma ação de **alto impacto e longa duração** —
mexe em código, cria commits, gasta tempo e contexto. O **controle do início é do usuário**, não uma
decisão que o modelo deva tomar sozinho ao interpretar uma frase como "acho que esse módulo tá meio
frágil" ou "dá uma olhada nesse código aí". A primitiva **`review` continua auto-invocável** — o
modelo pode auditar sob demanda e devolver um relatório de achados; é o **ciclo completo com
correções** (que decompõe os achados em sprints e mexe no código para consertá-los) que é
deliberado. Se você é o modelo e está lendo isto fora de um `/review-and-fix` explícito, **não
inicie o fluxo** — no máximo, faça a revisão pontual pedida (via `review`) e sugira que o usuário
rode `/review-and-fix` quando quiser conduzir o ciclo inteiro de correção.

## Pré-condições

Antes de orquestrar, confirme que existe:

- **As skills primitivas disponíveis** — `review`, `decompose`, `execute-sprint` e `verify-sprint`.
  Esta skill as chama; se alguma faltar, a fase correspondente não tem como rodar. (O ideal é que
  estejam empacotadas juntas no mesmo **plugin**.)
- **Um corpo de trabalho existente sob controle de versão** — o ciclo audita algo que **já existe** e
  os checkpoints **commitam por correção**. Sem versão, não há como isolar uma correção nem voltar
  atrás quando um gate reprova ou um mini review acha regressão.

Se o usuário chamou `/review-and-fix` sem indicar o alvo, tudo bem: pergunte **o que revisar** (o
repositório inteiro ou uma área específica) antes de disparar a primeira fase. Não presuma o escopo.

## Procedimento (a orquestração)

Siga as fases em ordem. Cada uma é uma **chamada à primitiva**, com o seu "porquê" para você julgar
bem quando o caso real fugir do roteiro. O princípio que atravessa tudo: **falha para o fluxo;
sucesso avança**.

### 1. Revisar — invocar `review` em escopo completo

Invoque a `review` sobre o **alvo indicado** (o repositório inteiro ou a área que o usuário apontou),
preferencialmente **em subagent**, para produzir o **relatório de achados priorizados** — cada
achado com arquivo, cenário de falha concreto e correção sugerida, ordenados por severidade.

Esta é a fase de **diagnóstico**: aqui não se corrige nada, só se levanta o que está errado. Se a
`review` **não achar nada relevante**, o ciclo termina aqui — reporte "nada a corrigir" em vez de
inventar correções para justificar o fluxo.

### 2. Apresentar os achados ao usuário — ponto de controle humano

O relatório de achados é um **ponto de decisão humana**, não uma lista de ordens de serviço
automáticas. **Apresente os achados ao usuário e espere a confirmação de quais corrigir.** O usuário:

- **confirma** quais achados viram correção agora,
- **ajusta prioridades** (a ordem da `review` é uma sugestão, não um decreto),
- pode **adiar** achados para "fases futuras" — nem todo achado precisa virar correção imediata.

Só os achados **aprovados** seguem para a decomposição. Adiar um achado é uma decisão legítima do
usuário: registre-o como "fase futura" e **não o transforme em sprint** agora. Fechar essa lista pelo
seu julgamento — corrigir tudo que a `review` apontou sem passar pelo usuário — é atropelar o
controle humano que esta fase existe para garantir.

### 3. Decompor — invocar `decompose` (um sprint de correção por achado)

Com os achados aprovados, invoque a `decompose` sobre eles para gerar os **sprints de correção**:
**um sprint por achado**. A decomposição os ordena com **justificativa** (severidade +
dependências + vitória rápida) e dá a cada um um **entregável verificável** — a **prova de
correção**: a evidência objetiva de que **aquele bug específico sumiu**.

**Um achado, um sprint** é deliberado: correções isoladas dão **checkpoint limpo** e **rollback
fácil**. Amontoar vários achados num sprint só embaralha a prova (qual correção quebrou o quê?) e
tira o isolamento que torna cada fix reversível sozinho.

### 4. Confirmar o plano com o usuário

Antes de executar qualquer correção, **apresente o plano de sprints de correção ao usuário e espere
aprovação**. Este é o **segundo ponto de controle humano**: o usuário aprova, reordena ou ajusta o
escopo das correções. É o último momento barato para corrigir o rumo — depois daqui começa a mexer
no código. Não pule este checkpoint "para ganhar tempo".

### 5. Loop de correção — um sprint por vez

Para cada sprint de correção, na ordem do plano, execute **este ciclo completo** antes de olhar o
próximo. A ordem interna importa: **conformidade antes de qualidade**.

1. **Executar — `execute-sprint`.** Invoque a `execute-sprint` para a próxima correção. Ela planeja,
   implementa **apenas o escopo daquela correção**, valida o entregável (a prova de que o bug sumiu)
   e commita.

2. **Gate de conformidade — `verify-sprint` (subagent independente).** Invoque a `verify-sprint`
   para julgar, **independente do executor**, se a correção entregue corresponde ao que o sprint de
   correção **definiu** — inclusive se a **prova exigida** ("o bug X sumiu") foi de fato produzida e
   **testa a coisa certa**, e não uma prova adjacente que passa sem exercitar o bug. É um **GATE**:
   - **CONFORME** → libera a etapa seguinte.
   - **NÃO CONFORME** ou **PARCIAL** → **pare e reporte**. Não avance, não feche a correção, não siga
     para o mini review. O gate reprovar é sinal de que a entrega desviou do combinado — ou a prova
     não prova o que devia. Seguir por cima disso propaga o desvio.

   Por que **antes** do mini review: uma correção pode estar bem-feita e ainda assim **não provar**
   que o bug sumiu. Verificar aderência primeiro evita gastar uma revisão de qualidade em algo que já
   está fora do combinado.

3. **Mini review — `review` em escopo pequeno.** Passado o gate, invoque a `review` sobre **apenas o
   diff daquela correção** (não o repo inteiro) para confirmar duas coisas: **(a)** que o bug de fato
   **sumiu** e **(b)** que **nada foi quebrado em volta** — que a correção não introduziu regressão
   no código adjacente. Este segundo ponto é o coração do ciclo de endurecimento: corrigir A e
   quebrar B silenciosamente é um retrocesso, não um progresso.

4. **Checkpoint.** Se a **execução**, o **gate** ou o **mini review** revelarem falha — inclusive uma
   **regressão** detectada pelo mini review —, **pare e reporte** ao usuário; **não avance
   automaticamente** para a próxima correção. Se tudo passou, siga para a próxima — idealmente com
   **contexto limpo** entre sprints (o que uma correção precisa saber está no seu prompt e no estado
   commitado, não na memória de conversa da anterior).

### 6. Fechamento verificado

**Não declare "resolvido" pela sensação.** Ao final, confirme, com prova:

- que **cada achado endereçado foi de fato corrigido** — a prova por sprint (o bug X sumiu) foi
  produzida e **re-executada do estado limpo**, não só relatada como verde,
- o **estado do repositório** (todas as correções commitadas, nada pela metade),
- as **checagens do projeto** (o que o `CLAUDE.md`/regras exigem),
- que **nada em volta regrediu** — um smoke do fluxo que essas correções tocam, de ponta a ponta,
  confirmando que endurecer um ponto não quebrou outro.

**Prova está no artefato, não na nota**: um achado só está fechado quando a correção está **no código
entregue** e a prova de que o bug sumiu foi **re-executada** — não quando um commit *diz* que
corrigiu. Cuidado com o "todas as correções verdes, pode fechar" quando a re-execução da prova não
aconteceu de fato.

O fechamento honesto é: "os achados A, B, C foram corrigidos e verificados (prova por sprint); os
achados D, E ficaram para fases futuras a seu pedido" — não um "acho que tá tudo resolvido". Se a
correção **fez novas questões surgirem** (um fix que revela outro problema), elas podem **originar
outro ciclo** — mas isso é uma nova rodada de `/review-and-fix`, não algo a emendar silenciosamente
neste fechamento.

## Formato de saída (painel de orquestração)

Conduza o fluxo mantendo o usuário orientado sobre **onde está** e **o que passou**. Ao reportar
progresso — e obrigatoriamente ao **parar** ou **fechar** —, use um painel como o de
[`assets/painel-orquestracao.md`](assets/painel-orquestracao.md):

```
# review-and-fix — <alvo>
**Fase atual:** <review | decompose | correção N/total | fechado>

## Achados (da review)
| # | Achado           | Severidade | Decisão do usuário   |
|---|------------------|------------|----------------------|
| 1 | <descrição>      | alta       | corrigir agora       |
| 2 | <descrição>      | média      | fase futura (adiado) |

## Correções (um sprint por achado aprovado)
| # | Correção (achado) | Execução | Gate (verify)  | Mini review (sumiu? quebrou algo?) | Estado     |
|---|-------------------|----------|----------------|------------------------------------|------------|
| 1 | <achado 1>        | ✅        | ✅ CONFORME     | ✅ bug sumiu / nada quebrou         | fechado    |
| 2 | <achado 3>        | ✅        | ✅ CONFORME     | ❌ regressão em volta               | PAROU AQUI |

## Checkpoints humanos
- [x] Achados apresentados e aprovados pelo usuário
- [x] Plano de correções aprovado pelo usuário

## Situação
<CONFORME e seguindo | PAROU na correção N, etapa <execução/gate/mini review> — motivo + o que reportar | FECHADO — achados corrigidos + verificados; adiados listados>
```

Quando o fluxo **para** num vermelho, o painel deve deixar claro **em qual correção**, **em qual
etapa** (execução/gate/mini review) e **por quê** — para o usuário decidir o próximo passo. Um "parou
e reportou" com o motivo concreto (ex.: "a correção do achado 3 passou o gate mas o mini review
detectou que quebrou o parsing adjacente") é um resultado **válido**, não um fracasso.

## Princípios (o núcleo, quando o roteiro não cobrir o caso)

- **Orquestrar, não reimplementar.** Cada fase é uma chamada à primitiva. Se você se pegar auditando,
  decompondo ou corrigindo código à mão aqui dentro, saiu do papel: delegue.
- **Um achado, um sprint.** Correções isoladas para **checkpoint limpo** e **rollback fácil**. Não
  amontoe achados num sprint só.
- **Prova por correção.** Cada sprint de correção só fecha com a **evidência de que aquele bug
  específico sumiu** — e o mini review confirma que **nada quebrou em volta**. Sem prova, não é
  correção fechada; é esperança.
- **Controle humano.** Os **achados** e o **plano de correção** são aprovados pelo usuário antes de
  executar. Adiar um achado é decisão legítima do usuário, não sua. O início do fluxo também é do
  usuário (disparo manual).
- **Checkpoint em cada fronteira.** Falha **para** o fluxo; sucesso **avança**. Gate de conformidade
  **antes** do mini review; mini review após cada correção; parada no vermelho — inclusive por
  regressão detectada.
- **Conformidade antes de qualidade.** `verify-sprint` (a correção provou o que prometeu?) roda
  **antes** do mini review (`review`) — porque uma correção bem-feita ainda pode não provar que o
  bug sumiu.
- **Fechamento é verificado, não sentido.** "Resolvido" exige prova: por sprint, no repo e nas
  checagens do projeto — não uma impressão.
- **Manual e deliberada.** Esta skill nunca é auto-invocada; o usuário decide o início.

## Fronteiras (o que esta skill NÃO faz)

- **Não constrói do zero** — isso é `build-project`. A `review-and-fix` **endurece o que já existe**
  via revisar-e-corrigir; erguer um projeto a partir de requisitos é o fluxo de orquestração irmão.
- **Não reimplementa `review`, `decompose` nem a execução** — cada uma dessas é a sua primitiva
  (`review`, `decompose`, `execute-sprint`, `verify-sprint`). Esta skill só as **encadeia**.
- **Não corrige achados que o usuário adiou** — os achados marcados como "fase futura" ficam de fora
  do ciclo atual; não vire sprint por conta própria só porque a `review` os apontou.
- **Não é auto-invocável** — só roda com `/review-and-fix` explícito. A primitiva `review` sozinha,
  essa sim, pode ser disparada pelo modelo para uma auditoria pontual.

## Variantes por tecnologia (futuro)

A orquestração é agnóstica de tecnologia por decisão: a **sequência** de fases e os **checkpoints**
não mudam entre um projeto de dados, uma API ou uma migração — o que muda são os comandos concretos
(como provar que um bug sumiu, como validar), que vivem nas primitivas e no `CLAUDE.md` do projeto.
Não há variantes de stack previstas para esta camada. Se algum dia surgir necessidade de um guia
específico, ele entra como `references/<tema>.md`, lido sob demanda — o núcleo (encadear
revisar→corrigir com checkpoints) permanece genérico.
