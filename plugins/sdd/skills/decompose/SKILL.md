---
name: decompose
description: >-
  Quebra um corpo de trabalho — uma especificação de projeto (saída da `spec`) ou um relatório de
  code review (saída da `review`) — em uma sequência de sprints: unidades de escopo fechado, com
  ordem justificada, dependências explícitas e, cada uma, um entregável verificável. Emite um índice
  da sequência e um prompt de sprint por unidade, prontos para a `execute-sprint`. A fonte é
  parâmetro: decompor uma spec em sprints de desenvolvimento e decompor um review em sprints de
  correção são a mesma operação. Use sempre que o usuário quiser planejar, organizar ou dividir um
  trabalho em fases/etapas/sprints. Dispare também por "/decompose" e quando o usuário disser "monte
  o roadmap", "divida isso em partes", "crie as sprints", "quebra isso em etapas" ou "organize as
  correções", mesmo sem a palavra "sprint". Não produz a especificação, não executa os sprints nem
  faz o review que os origina — apenas decompõe e sequencia. Aplica-se a qualquer domínio.
---

# decompose

Esta skill transforma um corpo de trabalho **a ser feito** em um **plano de sprints**: uma sequência
de unidades com escopo fechado, ordem justificada, dependências explícitas e, cada uma, um
**entregável verificável** — a prova de aceite que diz quando aquele sprint terminou. O produto é um
conjunto de prompts de sprint prontos para serem executados um a um pela `execute-sprint`.

É a etapa de **planejamento** do método de sprints. Ela **corta e sequencia**; não implementa (isso é
da `execute-sprint`) e não julga qualidade (isso é da `review`). É **genérica**: raciocina sobre
escopo, dependência e verificabilidade — não sobre linguagens, frameworks ou ferramentas. Os comandos
concretos (como validar, como commitar) pertencem ao projeto e entram só na execução.

## A fonte é parâmetro

A mesma operação serve a duas entradas:

- **Uma especificação** (requisitos + decisões — tipicamente a saída da `spec`): decompõe-se em
  **sprints de desenvolvimento**.
- **Um relatório de review** (achados priorizados — a saída da `review`): decompõe-se em **sprints de
  correção**.

Quebrar uma spec em desenvolvimento e quebrar um review em correções é o **mesmo procedimento** — o
que muda é a entrada, não o método. Por isso é uma skill só, não duas. Onde os dois casos divergem, o
texto abaixo aponta explicitamente ("quando a fonte é spec / quando é review").

## Pré-condições / parâmetros

Antes de decompor, tenha em mãos:

- **A fonte inteira** — a especificação ou o relatório de review. Leia-a por completo antes de cortar
  o primeiro sprint; sequência boa depende de enxergar as dependências, e dependência você só vê com
  o todo à vista.
- **As convenções do projeto** (`CLAUDE.md`, README, exemplos commitados), se já existirem — para que
  os sprints se alinhem ao que o projeto já assume e para saber o que conta como "verificável" ali.

A skill é **genérica**: não roda ferramenta nenhuma. Ela raciocina sobre **o que precisa ser feito, em
que ordem, e como se prova que cada pedaço ficou pronto**.

## Princípios de decomposição (o núcleo do valor)

Estes seis princípios são o que uma boa decomposição faz de diferente de uma lista de tarefas
qualquer. O procedimento adiante é a aplicação deles; entenda-os primeiro.

1. **Contrato antes de implementação.** Quando a fonte é uma spec, os sprints que definem o
   **contrato/interface** — schema, formato de dados, assinatura de API — vêm **antes** dos que
   consomem esse contrato. A razão é dependência real: nada pode depender do que ainda não existe, e
   fixar o contrato cedo evita que dois sprints depois briguem sobre o formato. Consumidor antes de
   contrato é retrabalho garantido.

2. **Fatias verticais e verificáveis.** Cada sprint entrega algo que **dá para checar** — uma
   validação, uma prova de comportamento — não meio trabalho que só faz sentido junto com o próximo. O
   tamanho da fatia se decide por um único critério: *"isto tem um entregável que dá para verificar
   sozinho?"* Se a resposta é não, a fatia está mal cortada — junte com o que a torna verificável, ou
   reparta até cada pedaço ter sua própria prova.

3. **Um achado, um sprint (quando a fonte é review).** Cada achado do review vira **um** sprint de
   correção isolado. Isso dá checkpoint limpo e rollback fácil: se a correção de um bug quebra algo, o
   estrago está contido em um sprint, não emaranhado com três correções não relacionadas. Não agrupe
   bugs distintos "para adiantar" — o custo de misturar aparece na hora de reverter.

4. **Ordem justificada, não arbitrária.** A sequência segue **dependências técnicas primeiro**. Entre
   itens independentes, ordene por **risco/severidade** (o mais grave ou mais incerto cedo, enquanto
   há espaço para reagir) e reserve uma **vitória rápida** no começo quando fizer sentido — algo
   trivial primeiro ajuda a pegar ritmo e a validar o encanamento. A justificativa da ordem é
   **explicitada**, não deixada implícita: quem executa precisa saber por que o Sprint 2 vem antes do
   3.

5. **Não antecipar escopo.** Cada sprint declara suas **restrições** — o que NÃO fazer, o que pertence
   a sprints futuros. Isso existe para impedir vazamento: sem restrição escrita, a execução tende a
   "adiantar" trabalho do próximo sprint e entregar algo maior, misturado, que ninguém revisou naquele
   contexto. A restrição é o que mantém a fatia fechada.

6. **Futuro registrado à parte.** O que fica fora do conjunto atual — o "para a v2", o "depois a
   gente vê" — vai para uma seção **"fora de escopo / fases futuras"**, nunca embutido num sprint do
   ciclo atual. Embutir futuro incha o sprint e embaralha o que é para agora com o que é para depois;
   registrar à parte preserva os dois.

## Procedimento

Siga os passos em ordem. Cada um traz o seu "porquê" para você julgar bem quando o caso real não se
encaixar exatamente no roteiro.

### 1. Ler a fonte inteira e as convenções

Leia a especificação ou o relatório de review **por completo**, junto com as convenções do projeto,
antes de cortar qualquer sprint. Cortar antes de ler o todo é como sequenciar sem enxergar as
dependências — você descobre tarde que o Sprint 2 precisava de algo do Sprint 5.

### 2. Identificar as unidades de trabalho e suas dependências

Liste as unidades candidatas e, para cada uma, de que ela **depende** (o que precisa existir antes) e
o que **depende dela**. Quando a fonte é um **review**, a unidade natural já vem dada: **cada achado é
uma unidade** (princípio 3). Quando é uma **spec**, procure as juntas naturais — onde um contrato é
definido, onde ele é consumido, onde uma camada termina e outra começa.

### 3. Sequenciar aplicando os princípios

Ordene as unidades: **contrato antes de consumo** (princípio 1), **dependências técnicas primeiro**, e
entre independentes por **risco/severidade e vitória rápida** (princípio 4). Confirme que cada unidade
é uma **fatia vertical verificável** (princípio 2) — se alguma não tiver entregável próprio checável,
ela está mal cortada: junte-a ao que a torna verificável ou reparta até cada pedaço ter sua prova.

### 4. Definir cada sprint

Para **cada** sprint, escreva quatro coisas:

- **Objetivo** — a mudança de estado que ele entrega, em uma frase.
- **Escopo** — o que fazer, concreto.
- **Restrições** — o que NÃO fazer / o que pertence a sprints futuros (princípio 5).
- **Entregável verificável** — a prova de aceite: a validação ou demonstração objetiva de que o
  comportamento-alvo de fato ocorre. Defina-a para ser **re-executável de forma independente e
  reproduzível do zero**: diga *como rodá-la a partir de um estado limpo* e *qual propriedade real
  ela exercita*. Uma prova que só passa em contexto — cache quente, mesmo processo, estado deixado
  por outro sprint, caminho feliz que nunca aciona a lógica sensível — é um entregável **mal
  definido**: o gate `verify-sprint` vai re-executá-la do zero, e ela precisa aguentar isso.

**Verificabilidade é o teste de corte.** Um sprint sem entregável checável está mal cortado — não o
emita assim. Se, ao definir o entregável, você perceber que a fonte pediu algo **vago demais para
virar prova** ("melhorar a performance", "deixar a UX melhor", sem nenhum critério objetivo), **não
invente um critério** para preencher o buraco: **sinalize** que aquele item precisa ser melhor
especificado (voltar à `spec`, ou perguntar ao usuário) antes de virar sprint. Um sprint sem critério
de aceite é um sprint que ninguém sabe quando termina.

### 5. Registrar ordem, dependências e o que ficou fora

Monte o **índice**: a ordem dos sprints, o entregável-resumo de cada um, as dependências e a
**justificativa da sequência** (princípio 4). Separe o que ficou **fora de escopo / fases futuras**
(princípio 6) — inclusive itens que a própria fonte marcou como "para depois". Um item explicitamente
adiado na fonte vai para essa seção, **não** para um sprint.

### 6. Emitir os prompts de sprint

Produza a saída no formato fixo (abaixo): o índice, um prompt por sprint pronto para a
`execute-sprint`, e a seção de fora de escopo. Quando a fonte é um **review**, cada prompt **referencia
o achado que corrige** e o entregável inclui a **prova de que aquele bug específico sumiu** — não só
"os testes passam", mas a demonstração de que o cenário de falha descrito no achado não ocorre mais.

## Formato de saída

Use este template (os `< >` são marcadores a preencher). O esqueleto vazio também está em
[`assets/sprint-plan-template.md`](assets/sprint-plan-template.md) para copiar.

```
# Plano de Sprints — <projeto / alvo>
**Fonte:** <especificação X | relatório de review Y>

## Índice e sequência
| # | Sprint            | Entregável (resumo)          | Depende de | Por que nesta posição   |
|---|-------------------|------------------------------|------------|-------------------------|
| 1 | <título>          | <prova-resumo>               | —          | <justificativa>         |
| 2 | <título>          | <prova-resumo>               | 1          | <justificativa>         |

<Sequência — um parágrafo com a lógica geral da ordem: contrato antes de consumo, dependências
técnicas, e por que os itens independentes ficaram nesta ordem (risco/severidade, vitória rápida).>

---

## Sprint 1 — <título>

**Contexto:** <de onde este sprint vem: o trecho da spec que ele realiza, ou o achado do review que
ele corrige — cite o achado quando a fonte for review>
**Objetivo:** <a mudança de estado que este sprint entrega, em uma frase>

### Escopo
- <o que fazer — concreto>

### Restrições
- <o que NÃO fazer / o que pertence a sprints futuros — para não vazar escopo>

### Entregável (prova verificável)
- <a prova de aceite: a validação ou demonstração objetiva de que o comportamento-alvo ocorre>
- <quando a fonte é review: a prova de que aquele bug específico sumiu — o cenário de falha do
  achado não se reproduz mais>

### Commit
- <mensagem de commit sugerida referenciando o sprint — quando o projeto usa controle de versão>

---

## Sprint 2 — <título>
<mesma estrutura>

---

## Fora de escopo / fases futuras
- <o que ficou de fora do ciclo atual, com uma linha de por quê / quando entra>
- <inclui itens que a fonte marcou explicitamente como "para depois", e itens vagos demais que
  precisam voltar à spec antes de virar sprint>
```

Se algum item da fonte for **vago demais para virar entregável verificável**, não force um sprint:
liste-o em "fora de escopo / fases futuras" com a nota de que precisa ser melhor especificado, ou
sinalize antes de emitir o plano. Sinalizar uma lacuna é um resultado válido — inventar um critério de
aceite que a fonte não deu é que não é.

## Princípios (o núcleo, quando o roteiro não cobrir o caso)

- **Verificabilidade é obrigatória** — um sprint sem entregável checável está mal cortado; refaça o
  corte ou sinalize a lacuna. Nunca emita um sprint sem critério de aceite.
- **Contrato primeiro** (para specs); **um achado, um sprint** (para reviews).
- **Restrições explícitas** em cada sprint — é o que impede o vazamento de escopo na execução.
- **Ordem com justificativa** — dependência técnica primeiro; entre independentes, risco/severidade e
  vitória rápida. A justificativa é escrita, não implícita.
- **Futuro à parte** — o que é "para depois" vai para a seção própria, nunca embutido num sprint atual.
- **Genérica** — sem ferramentas ou stacks embutidas; o projeto pluga isso na execução.

## Fronteiras (o que esta skill NÃO faz)

- **Não produz a especificação** a partir de requisitos brutos — isso é da `spec`, que normalmente
  roda antes e alimenta esta.
- **Não executa** os sprints — isso é da `execute-sprint`, que consome os prompts que esta emite.
- **Não faz o review** que origina os sprints de correção — isso é da `review`. Esta skill recebe o
  relatório pronto e o decompõe.
- **Não verifica conformidade nem qualidade** — julgar se a entrega bate com o definido é da
  `verify-sprint`; julgar se está bem-feita é da `review`. Aqui só se **decompõe e sequencia**; não se
  implementa nem se audita.

## Variantes por tecnologia (futuro)

A versão genérica não precisa de recursos por stack — a decomposição é agnóstica: raciocinar sobre
escopo, dependência e verificabilidade não muda entre Terraform, Python ou uma migração de dados. Se
mais adiante surgir necessidade de guias específicos (o que costuma ser uma "fatia verificável" em tal
tecnologia), cada um entra como `references/<tecnologia>.md`, lido sob demanda. O núcleo permanece
genérico.
