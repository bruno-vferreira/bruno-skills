---
name: run-sprints
disable-model-invocation: true
description: >-
  Orquestra o método SDD ponta a ponta com estado persistido em docs/sdd/, a partir de um de dois
  pontos de entrada: do zero (spec → decompose) ou endurecimento de código existente
  (review-quality em escopo completo → achados aprovados → decompose). Dali em diante, por
  sprint: execute-sprint em subagent isolado → verify-sprint como GATE → mini review, com
  checkpoint humano em cada fronteira, parada no vermelho e fechamento verificado. Fluxo de alto
  impacto e longa duração — roda apenas via "/run-sprints" explícito; as primitivas continuam
  auto-invocáveis avulsas. Agnóstica de domínio e tecnologia.
argument-hint: "[alvo ou objetivo]"
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.5.0"
---

# run-sprints

Orquestra as skills primitivas do método de sprints, a partir de um de dois pontos de entrada:

- **Do zero** — nada construído ainda: **spec → decompose** gera sprints de desenvolvimento.
- **Endurecimento** — código/repo já existe e precisa de correção: **review-quality (escopo
  completo) → achados aprovados → decompose** gera sprints de correção, um por achado.

A partir do decompose, o procedimento é **idêntico** nos dois casos: por sprint, **execute-sprint
(em subagent) → verify-sprint [GATE] → mini review**, checkpoint humano em cada fronteira, fechando
com uma checagem verificada. Não reimplementa nenhuma fase — sequencia, insere checkpoints, e
**para no vermelho** em vez de seguir sobre uma falha.

Genérica: não conhece linguagem, framework ou ferramenta. Comandos concretos vivem no `CLAUDE.md`
do projeto, responsabilidade das primitivas. Esta skill só decide qual etapa vem agora e se é
seguro avançar.

## Por que o disparo é manual

`disable-model-invocation: true` é deliberado: rodar o ciclo inteiro mexe em código, gera commits e
consome tempo — o início é decisão do usuário, nunca inferida de uma frase solta como "acho que vou
construir X".

## O estado vive em arquivos, não na conversa

Todo o estado do ciclo é persistido em `docs/sdd/` e mantido pelas primitivas e seus scripts:

| Artefato | Quem escreve |
|---|---|
| `docs/sdd/spec-<tema>.md` | `spec` |
| `docs/sdd/sprints/00-plano.md` + `NN-<slug>.md` | `decompose` |
| `docs/sdd/status.md` (painel) | `sdd_status.py` (nunca à mão) |
| `TECH_DEBT.md` | `tech_debt.py` (nunca à mão) |

Consequências operacionais:

- **Disciplina de path.** Ao delegar ou invocar uma fase, passe **caminhos**, nunca o conteúdo —
  quem executa lê o arquivo. Conteúdo colado na delegação é ruído duplicado no contexto.
- **`/clear` é seguro nos checkpoints.** O histórico não carrega estado; após a aprovação do plano
  (fim da fase conversacional) — e a cada poucos sprints, se a sessão crescer — **sugira ao usuário
  rodar `/clear`**. Retomada barata: reler `docs/sdd/status.md` + `00-plano.md` e continuar do
  próximo sprint não-fechado. Isso substitui a auto-compactação (que degrada na hora errada) por um
  corte deliberado e sem perdas.
- **No chat, só o delta.** O painel completo fica em `status.md`; a conversa recebe a linha que o
  `sdd_status.py set` imprime ("Sprint 03: conforme → fechado") — não re-renderize a tabela.

## Qual entrada usar

- Requisitos ainda soltos ou nada construído → comece pela **spec**.
- Código já existe e a pergunta é "está certo?", "conserta isso", "audita e corrige" → comece pela
  **review-quality**.
- Ambíguo → pergunte antes de disparar a primeira fase; não presuma.

## Pré-condições

- Skills primitivas (`spec`, `decompose`, `execute-sprint`, `verify-sprint`, `review-quality`) e
  os subagents do plugin (`sdd:sprint-executor`, `sdd:verifier`, `sdd:reviewer`) disponíveis.
- Repositório/corpo de trabalho sob controle de versão — checkpoints commitam por sprint.

## Procedimento

Fases: **1. entrada → 2. decompose → 3. aprovação do plano → 4. loop por sprint → 5. fechamento.**
O progresso vive em `docs/sdd/status.md` — consulte-o (não a memória) para saber onde o ciclo está.

**1. Entrada.**
- *Do zero:* invoque `spec`. Fase conversacional — pode levar várias trocas. **Checkpoint:** só
  avance quando o usuário considerar a especificação fechada (gravada em `docs/sdd/`), não pela
  sua própria avaliação.
- *Endurecimento:* invoque `review-quality` em escopo completo sobre o alvo indicado (pergunte o
  alvo se não foi dito) — ela roda em subagent próprio. Apresente os achados — **checkpoint
  humano**: o usuário confirma quais corrigir, reprioriza (a ordem do relatório é sugestão, não
  decreto) ou adia; só os aprovados seguem adiante. Se ela não achar nada relevante, o ciclo
  termina aqui: reporte "nada a corrigir" em vez de inventar correção para justificar o fluxo.

**2. Decompose.** Invoque `decompose` sobre a spec fechada (por caminho) ou os achados aprovados.
Ela grava `00-plano.md` + um arquivo por sprint e gera o painel inicial — no endurecimento, um
sprint de correção por achado (checkpoint limpo, rollback fácil), e o entregável prova que aquele
bug específico sumiu.

**3. Aprovação do plano.** Apresente o índice do plano (não os arquivos inteiros) e espere
aprovação do usuário antes de executar qualquer coisa — último ponto barato para corrigir rumo.
Não pule para "ganhar tempo". Aprovado, **sugira `/clear`** — a fase conversacional acabou; o
ciclo continua do estado em arquivos.

**4. Loop de execução** — por sprint, nesta ordem (conformidade antes de qualidade):

  a. **Executar em subagent:** delegue ao agent `sdd:sprint-executor`, passando **o caminho** do
     arquivo do sprint (`docs/sdd/sprints/NN-*.md`) e nada mais que 1–2 linhas de contexto. Ele
     planeja, implementa só aquele escopo, valida, commita e mantém o status via script; o
     contexto dele morre com ele — só o resumo volta. A aprovação do plano no passo 3 cobre o
     plano do sprint; o executor não para para reaprovar — se surgir decisão de design que o plano
     não cobre, ele **para e reporta**, e a decisão volta ao usuário aqui. *(Sem o agent
     disponível, invoque `execute-sprint` inline — mesmo contrato.)*

  b. **`verify-sprint`** (subagent independente) — GATE de conformidade: o entregue corresponde ao
     que o sprint definiu? Passe o **caminho** da definição. Escopo cumprido, restrições
     respeitadas, entregável comprovado.
     - CONFORME → `sdd_status.py set <N> conforme` e segue para 4c.
     - NÃO CONFORME / PARCIAL → `sdd_status.py set <N> parou --nota "gate: <motivo>"`, **pare e
       reporte**. Não feche o sprint, não vá ao mini review.

     Roda antes do mini review porque um sprint pode estar bem-feito e ainda assim fora do escopo —
     checar aderência primeiro evita gastar revisão de qualidade em algo já descartado.

  c. **`review-quality`** em escopo pequeno — só o diff do sprint. No endurecimento, confirma duas
     coisas: o bug de fato sumiu, **e** nada foi quebrado em volta (o coração do endurecimento:
     corrigir A e quebrar B silenciosamente é retrocesso, não progresso). Do zero, checa qualidade
     (bugs, lógica, contrato × comportamento).

  d. **Checkpoint.** Sucesso nas três etapas → `sdd_status.py set <N> fechado` e próximo sprint —
     o subagent seguinte nasce limpo por construção (usa o arquivo do sprint e o estado commitado,
     não a memória da conversa). Falha em qualquer etapa, inclusive regressão detectada → status
     `parou` com nota, **pare e reporte** — não avance automaticamente. Se a sessão estiver longa,
     este é o outro ponto natural para sugerir `/clear`.

**5. Fechamento verificado.** Não declare "pronto"/"resolvido" por sensação. Confirme com prova:
- estado do repositório (tudo commitado, nada pela metade) e painel sem sprint aberto;
- checagens do projeto (`CLAUDE.md`/regras);
- *do zero:* `review-quality` final em escopo completo — inconsistências entre camadas, integração
  entre sprints, o todo contra o contrato original — o que os mini reviews locais não veem; achados
  dela **não são corrigidos aqui**, encaminhe para um novo `/run-sprints` (entrada endurecimento);
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

O painel é `docs/sdd/status.md` — mantido pelo script, nunca redesenhado na conversa. No chat:
a linha-delta de cada transição de status e, ao **parar**, exatamente **qual sprint**, **qual
etapa** (execução/gate/mini review) e **por quê** — "parou e reportou com motivo concreto" é
resultado válido, não fracasso. Ao **fechar**, o resumo do fechamento verificado (item 5).

## Fronteiras

- Não implementa sprints (`execute-sprint`/`sprint-executor` fazem isso) nem audita
  (`review-quality` faz isso).
- Não especifica, decompõe ou revisa por conta própria — só encadeia as primitivas.
- Não corrige achados fora do ciclo aprovado — achados adiados ficam de fora, não viram sprint por
  conta própria.
- Não é auto-invocável — só roda com `/run-sprints` explícito. As primitivas continuam
  auto-invocáveis para uso pontual (ex.: uma `review-quality` avulsa, sem o ciclo completo).
