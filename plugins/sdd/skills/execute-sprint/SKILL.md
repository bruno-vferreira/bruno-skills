---
name: execute-sprint
description: >-
  Executa um único sprint de desenvolvimento de forma disciplinada: planeja antes de agir,
  implementa apenas o escopo do sprint, valida o entregável com prova objetiva e faz commit —
  parando e reportando se a validação falhar. Use sempre que o usuário for executar, rodar ou
  implementar um sprint, uma fase, uma etapa de um plano/roadmap, ou um item de uma lista de
  tarefas com escopo e critério de aceite definidos — mesmo que ele não diga a palavra "sprint".
  Aplica-se a qualquer domínio (código, infraestrutura, documentação, dados). Aplica-se também a
  sprints de correção originados de code review.
---

# execute-sprint

Esta skill executa **um** sprint de um plano incremental, do começo ao fim, com disciplina de
checkpoint. Ela transforma um prompt de sprint — escopo + restrições + entregável verificável —
em trabalho implementado, validado por prova objetiva e commitado. Se a validação falhar, ela
**para e reporta**, em vez de seguir por cima do erro.

É a unidade de execução do método de sprints. É **genérica**: não embute nenhuma linguagem,
framework ou ferramenta. Os comandos concretos (como validar, como commitar) vivem no `CLAUDE.md`
do projeto e nas regras associadas — esta skill chama "o comando de validação do projeto", nunca
uma ferramenta específica.

## Pré-condições

Antes de executar, confirme que existe:

- **Uma definição de sprint** com, no mínimo: o **escopo** (o que fazer), as **restrições** (o
  que NÃO fazer / não antecipar) e um **entregável verificável** (o critério de aceite — a prova
  que o sprint exige). Se qualquer um desses três estiver ausente ou ambíguo, resolva isso
  **antes** de tocar em código: pergunte, ou aponte a lacuna no documento do sprint.
- **Controle de versão ativo** no repositório — o commit ao final depende disso.

Se a definição do sprint estiver incompleta a ponto de você não saber o que provar no final,
não improvise um critério: sinalize e peça para completar. Executar sem entregável claro é
executar sem saber quando parar.

## Procedimento

Siga os passos em ordem. Cada um existe por um motivo — o motivo está descrito para você poder
julgar bem quando o caso real não se encaixar exatamente no roteiro.

### 1. Ler o contexto do projeto primeiro

Antes de planejar qualquer coisa, leia os documentos de convenção do projeto (tipicamente
`CLAUDE.md` e as regras que ele referencia) e o prompt do sprint. **Não assuma convenções de
memória** — o comando de teste, o estilo de commit, as ferramentas e os limites são propriedade
do projeto, e mudam de projeto para projeto. Ler primeiro evita retrabalho e evita violar uma
regra que você poderia ter conhecido.

### 2. Planejar antes de agir

Produza um plano do que **este** sprint vai fazer — quais arquivos, qual abordagem, como o
entregável será provado. Quando o ambiente suportar (ex.: plan mode do Claude Code), **apresente
o plano para aprovação antes de editar qualquer arquivo**. Planejar antes barateia o erro: é mais
fácil corrigir um plano do que desfazer um trabalho.

Se houver uma **decisão de design com mais de uma opção viável**, não decida sozinho. Apresente
as opções com seus trade-offs e aguarde a escolha. Uma suposição silenciosa aqui vira dívida
depois; uma pergunta agora custa uma frase. Decisão de design é pergunta, não palpite.

### 3. Implementar apenas o escopo do sprint

Implemente o que o sprint pede — **e nada além**. Não antecipe trabalho de sprints futuros, seja
para "adiantar", seja para fazer uma verificação passar. As restrições declaradas são parte do
contrato: respeitá-las é parte de fazer o sprint certo, não uma limitação a contornar.

Se cumprir o escopo exigir genuinamente tocar em algo fora dele, **sinalize a tensão** em vez de
expandir em silêncio — descreva o que o escopo parece exigir por fora e deixe a decisão explícita.
O risco de "adiantar" é entregar algo maior e diferente do que foi combinado, que ninguém pediu e
ninguém revisou naquele contexto.

### 4. Validar o entregável com prova objetiva

Rode as checagens do projeto (testes, lint, build — o que o `CLAUDE.md` definir). Mas passar nas
ferramentas **não é** o aceite: é o piso. O aceite é a **evidência específica que o entregável do
sprint pede** — a demonstração de que o comportamento-alvo de fato ocorre.

"As ferramentas passaram" prova que nada quebrou; não prova que o que o sprint prometia acontece.
Produza a prova que o próprio sprint define: exercite o caminho novo e observe o resultado, mostre
a saída esperada, demonstre o efeito. **Prova, não sensação** — "parece pronto" nunca é aceite.

A prova também tem de ser **reproduzível do zero**: ela não pode passar só por causa de estado que
você deixou (um cache quente, um arquivo de uma rodada anterior, o mesmo processo que acabou de
escrever o valor). Rode-a a partir de um **estado limpo**; quando o comportamento é sensível a
concorrência, ordem ou reinício, exercite-o sob essas condições. Senão você entrega um verde que só
existe no seu contexto. O gate (`verify-sprint`) vai **re-executar** essa prova de forma independente —
uma prova que só passa "aqui e agora" será reprovada lá.

### 5. Checkpoint — decidir avançar

Este é o momento de decisão. Compare o resultado com **cada** item do entregável.

- **Se todos os itens passarem:** escreva um resumo curto do que foi feito e do resultado das
  checagens, e **faça o commit** com uma mensagem descritiva que referencie o sprint.
- **Se qualquer item falhar: PARE.** Não commite, não avance para o próximo passo, não tente
  "consertar por cima" sem entender. Reporte com clareza: **o que** falhou, a **causa provável** e
  **o que precisa ser decidido ou corrigido**. Então aguarde.

Parar no vermelho não é desistir — é recusar-se a construir sobre uma base que você sabe estar
quebrada. Um commit em cima de uma validação que falhou esconde o problema em vez de resolvê-lo,
e custa muito mais caro depois.

### 6. Não gerar resumo persistente paralelo

Não crie um arquivo de "memória" ou um resumo de handoff para a próxima sessão. **O estado é o
commit + os arquivos** — a próxima execução relê do repositório, que é a fonte de verdade. Se o
sprint produziu uma decisão de design nova que precisa sobreviver, registre-a nos documentos do
próprio projeto (ex.: `CLAUDE.md`, ADR), não em um resumo solto que vai divergir do código.

## Formato de saída

Ao final, entregue:

- **Um resumo de execução:** o que foi implementado, o resultado das checagens e a **evidência do
  entregável** — ou, em caso de falha, o relatório do que impediu o avanço (o quê, a causa, a
  decisão pendente).
- **Um commit** com mensagem descritiva referenciando o sprint — **apenas** quando o entregável
  passou.
- **Nenhum artefato de memória** ou resumo paralelo aos documentos do projeto.

## Princípios (o núcleo, quando o roteiro não cobrir o caso)

- **Escopo fechado** — implemente o sprint, nada além.
- **Prova, não sensação** — o entregável define a evidência; "parece pronto" não é aceite.
- **Parar no vermelho** — falha de validação interrompe e reporta; não se segue por cima.
- **Planejar antes de agir** — decisão de design vira pergunta, não suposição.
- **Corrigir na origem** — se o próprio prompt/plano tiver uma inconsistência, sinalize para
  corrigir o documento, não improvise um contorno que mascara o defeito.
- **Genérica** — nenhuma ferramenta ou linguagem embutida; o projeto pluga isso via `CLAUDE.md`.

## Fronteiras (o que esta skill NÃO faz)

Executa **um** sprint por invocação. Fora disso:

- **Não decompõe** um projeto em sprints — isso é da skill `decompose`.
- **Não audita** código em busca de bugs — isso é da skill `review`.
- **Não é o juiz independente de conformidade.** A auto-verificação daqui ("rodei a prova do
  entregável e passou") é do executor. O julgamento **independente** de se o entregue corresponde
  ao definido é da `verify-sprint`, um subagent cego ao raciocínio do executor, que atua como
  gate **depois** desta skill.
- **Não orquestra** múltiplos sprints em sequência — isso é das skills de orquestração
  (`build-project` / `review-and-fix`), que chamam esta uma vez por sprint.

## Variantes por tecnologia (futuro)

A versão genérica não precisa de recursos empacotados. Se, mais adiante, forem criadas variantes
por stack, cada uma entra como `references/<tecnologia>.md` descrevendo os comandos de validação e
commit daquela tecnologia. O núcleo genérico permanece idêntico; a referência é lida sob demanda.
