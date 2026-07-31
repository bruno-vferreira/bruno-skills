---
name: decompose
description: >-
  Quebra um corpo de trabalho — especificação (saída da `spec`), relatório de review (saída da
  `review-quality`) ou backlog de débito técnico (TECH_DEBT.md) — numa sequência de sprints
  gravada em docs/sdd/sprints/: escopo fechado, ordem justificada, dependências explícitas e
  entregável verificável, um arquivo por sprint, prontos para a `execute-sprint`. Use para
  planejar, organizar ou dividir trabalho em fases/sprints: "monte o roadmap", "divida isso em
  partes", "organize as correções". Não especifica, não executa nem revisa — só decompõe e
  sequencia, em qualquer domínio.
argument-hint: "[fonte]"
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.5.0"
---

# decompose

Transforma um corpo de trabalho a ser feito em um **plano de sprints**: unidades de escopo fechado,
ordem justificada, dependências explícitas e, cada uma, um **entregável verificável** — a prova de
aceite que diz quando o sprint terminou. Grava o plano em arquivos sob `docs/sdd/sprints/`, prontos
para a `execute-sprint`.

É a etapa de **planejamento**: corta e sequencia; não implementa (`execute-sprint`) e não julga
qualidade (`review-quality`). Genérica: raciocina sobre escopo, dependência e verificabilidade —
não sobre stack. Comandos concretos entram só na execução.

## A fonte é parâmetro

A mesma operação serve a três entradas:
- **Especificação** (saída da `spec`, em `docs/sdd/spec-*.md`) → **sprints de desenvolvimento**.
- **Relatório de review** (saída da `review-quality`) → **sprints de correção**.
- **Backlog de débito técnico** (`TECH_DEBT.md`, alimentado por `execute-sprint` e
  `review-quality`) → **sprints de refatoração/correção** dos itens selecionados.

Mesmo procedimento nos três casos — o que muda é a entrada, não o método. Onde divergem, o texto
abaixo marca "quando a fonte é spec / review / backlog".

Fonte backlog **não decompõe o arquivo inteiro de uma vez**: liste os itens abertos com
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tech_debt.py" list`, apresente-os ao usuário (com o campo
"escopo estimado" de cada um) e decomponha só os que ele selecionar — mesmo princípio de controle
humano que `run-sprints` já aplica aos achados de review. Itens "pontuais" raramente precisam de
sprint próprio (a expectativa é resolução incidental pela `execute-sprint` quando alguém voltar
àquele arquivo); quem tipicamente chega aqui são os marcados **amplo**.

## Pré-condições

- **A fonte inteira**, lida por completo antes de cortar o primeiro sprint — sequência boa depende
  de enxergar dependências, e dependência só se vê com o todo à vista.
- **Convenções do projeto** (`CLAUDE.md`, README, exemplos commitados), se existirem — para alinhar
  os sprints e saber o que conta como "verificável" ali.

## Princípios

1. **Contrato antes de implementação** (specs). Sprints que definem contrato/interface — schema,
   formato de dados, assinatura de API — vêm antes dos que o consomem. Nada depende do que ainda
   não existe; fixar o contrato cedo evita que dois sprints depois briguem sobre formato.

2. **Fatias verticais e verificáveis.** Cada sprint entrega algo checável sozinho, não meio
   trabalho que só faz sentido junto com o próximo. Critério: "isto tem entregável que dá para
   verificar sozinho?" Se não, junte com o que a torna verificável, ou reparta até ter.

3. **Um achado, um sprint** (reviews e itens de backlog). Cada achado ou item de débito técnico
   vira um sprint isolado — checkpoint limpo, rollback fácil. Não agrupe itens distintos para
   adiantar; o custo aparece na hora de reverter. Exceção: itens de backlog genuinamente
   acoplados (a mesma refatoração ampla toca as mesmas classes) podem formar um sprint só, desde
   que a fatia continue verificável (princípio 2).

4. **Ordem justificada, não arbitrária.** Dependências técnicas primeiro; entre itens
   independentes, risco/severidade (o mais grave/incerto cedo) e uma vitória rápida no começo
   quando fizer sentido. A justificativa da ordem é sempre escrita, nunca implícita.

5. **Não antecipar escopo.** Cada sprint declara restrições — o que NÃO fazer, o que é de sprints
   futuros. Sem isso, a execução tende a "adiantar" trabalho não revisado naquele contexto.

6. **Futuro registrado à parte.** O que fica fora do ciclo atual vai para "fora de escopo / fases
   futuras", nunca embutido num sprint — embutir incha o sprint e embaralha agora com depois.

## Procedimento

**1. Ler a fonte inteira e as convenções.** Cortar antes de ver o todo é sequenciar sem enxergar
dependências — descobre-se tarde que o Sprint 2 precisava de algo do Sprint 5.

**2. Identificar unidades e dependências.** Liste candidatas e, para cada uma, do que ela depende e
o que depende dela. Fonte review ou backlog: cada achado/item já é uma unidade (princípio 3), exceto
itens de backlog acoplados entre si. Fonte spec: procure as juntas naturais — onde um contrato é
definido, onde é consumido, onde uma camada termina.

**3. Sequenciar aplicando os princípios.** Contrato antes de consumo, dependências técnicas
primeiro, risco/severidade e vitória rápida entre independentes. Confirme que cada unidade é fatia
vertical verificável — senão, corte de novo.

**4. Definir cada sprint** com quatro campos:
- **Objetivo** — a mudança de estado entregue, em uma frase.
- **Escopo** — o que fazer, concreto.
- **Restrições** — o que NÃO fazer / o que é de sprints futuros.
- **Entregável verificável** — a prova de aceite, definida para ser **re-executável do zero e
  reproduzível**: como rodá-la a partir de estado limpo, e qual propriedade real ela exercita. Uma
  prova que só passa em contexto (cache quente, mesmo processo, estado deixado por outro sprint,
  caminho feliz que nunca aciona a lógica sensível) está mal definida — `verify-sprint` vai
  re-executá-la do zero.

**Verificabilidade é o teste de corte.** Se a fonte pediu algo vago demais para virar prova
("melhorar a performance", "deixar a UX melhor", sem critério objetivo), não invente um critério —
sinalize que o item precisa voltar à `spec` ou ao usuário antes de virar sprint.

**5. Registrar ordem, dependências e o que ficou fora.** Monte o índice com a justificativa da
sequência (princípio 4). Separe "fora de escopo / fases futuras" — inclusive itens que a própria
fonte já marcou como "para depois"; eles não viram sprint.

**6. Gravar o plano em arquivos.** O plano vive no repositório, não na conversa:
- `docs/sdd/sprints/00-plano.md` — índice, sequência com justificativa, fora de escopo.
- `docs/sdd/sprints/NN-<slug>.md` — um arquivo por sprint, começando com `# Sprint NN — <título>`
  seguido de `Status: pendente` na linha seguinte (é essa linha que `sdd_status.py` mantém).
- Após gravar, rode `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdd_status.py" render` para gerar o
  painel inicial (`docs/sdd/status.md`).

No chat, apresente **só o índice** (tabela de sequência + justificativa + fora de escopo) e os
caminhos dos arquivos — o conteúdo integral dos sprints está nos arquivos; não o duplique na
conversa. Fonte review: cada arquivo de sprint referencia o achado que corrige, e o entregável
prova que aquele bug específico sumiu — não só "os testes passam".

## Formato de saída

Use o esqueleto em [`assets/sprint-plan-template.md`](assets/sprint-plan-template.md) como guia
adaptável para os dois tipos de arquivo (índice e sprint). Se algum item da fonte for vago demais
para virar entregável verificável, não force um sprint: liste-o em "fora de escopo" no
`00-plano.md` com nota de que precisa ser melhor especificado. Sinalizar a lacuna é resultado
válido; inventar critério de aceite que a fonte não deu não é.

## Fronteiras

- Não produz a especificação a partir de requisitos brutos — isso é da `spec`.
- Não executa os sprints — isso é da `execute-sprint`, que consome os arquivos gravados aqui.
- Não faz o review que origina sprints de correção — isso é da `review-quality`.
- Não alimenta o `TECH_DEBT.md` — só o lê como fonte quando o usuário pedir. Quem registra itens
  ali é `execute-sprint` e `review-quality`, no curso do trabalho delas.
- Não verifica conformidade nem qualidade — `verify-sprint` julga aderência, `review-quality`
  julga qualidade. Aqui só se decompõe e sequencia.
