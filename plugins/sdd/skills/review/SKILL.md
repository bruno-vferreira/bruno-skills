---
name: review
description: >-
  Audita código, configuração ou documentação em busca de problemas que linters e validadores não
  pegam: divergências entre o contrato (schema, README, spec) e o comportamento real, bugs de
  lógica, suposições não verificadas e inconsistências entre camadas. Produz um relatório de
  achados priorizados por severidade — com arquivo, cenário de falha concreto e correção sugerida —
  e lista também o que está correto. O escopo é parâmetro: o diff de um sprint (mini review) ou o
  repositório inteiro. Use sempre que o usuário pedir uma revisão, um code review, uma auditoria,
  uma checagem de qualidade ou consistência, ou perguntar 'isto está correto? está bem-feito?'
  sobre um código ou um repositório — e também ao final de um sprint, para revisar o que acabou de
  ser implementado. Não corrige os achados nem verifica conformidade ao que o sprint pediu (isso é
  da verify-sprint); aqui se julga qualidade. Preferencialmente executada em subagent. Aplica-se a
  qualquer domínio.
---

# review

Esta skill **audita** um corpo de trabalho — código, configuração ou documentação — em busca dos
problemas que as ferramentas automáticas **não** detectam: divergências entre o que o contrato
promete e o que o código faz, bugs de lógica, suposições não verificadas e inconsistências entre
camadas. Ela produz um **relatório de achados** priorizados por severidade, cada um com
localização, cenário de falha concreto e correção sugerida — e reconhece também o que está
**correto**, para que uma "correção" futura não quebre o que já funciona.

É a etapa de **qualidade** do método de sprints. Ela **encontra e descreve**; não corrige (isso
vira sprints via `decompose` e é executado por `execute-sprint`). É **genérica**: não conhece
ferramentas ou stacks específicas — raciocina sobre contrato e lógica, não sobre a sintaxe de uma
tecnologia.

**O escopo é parâmetro.** A mesma skill roda sobre o diff de um único sprint (uma revisão pequena,
"mini review") ou sobre o repositório inteiro (revisão completa). O procedimento é o mesmo; muda a
abrangência.

## Por que roda em subagent

Uma revisão lê muitos arquivos e cruza informações entre eles, gerando bastante conteúdo
intermediário que **não precisa** sobreviver — só o **relatório final** interessa. Rodar a revisão
em um **subagent** isola esse trabalho pesado: o contexto principal recebe apenas os achados, e
permanece limpo. É o caso de uso canônico de subagent (isolar tarefa volumosa cujo material
intermediário é descartável).

Se o ambiente não tiver subagents, a skill ainda funciona no contexto principal — apenas sem o
benefício do isolamento. Em subagent, retorne o relatório final como um resumo estruturado ao
contexto principal.

## Pré-condições / parâmetros

Antes de revisar, tenha claro:

- **O escopo do review** — um conjunto de arquivos, um diff/commit específico (mini review de um
  sprint) ou o repositório inteiro. Se estiver ambíguo, confirme antes de começar: revisar o repo
  inteiro quando pediram só o diff de um sprint gera ruído e desperdício; revisar só o diff quando
  queriam o repo inteiro deixa passar problema.
- **Os documentos de contrato** do projeto — schema, README, spec, convenções (`CLAUDE.md`),
  exemplos commitados. São eles que dizem "o que é prometido"; sem eles você só consegue julgar o
  código contra si mesmo, não contra o que ele deveria fazer.

A skill é **genérica**: ela não roda ferramenta nenhuma nem conhece a sintaxe de uma stack. Ela
raciocina sobre **contrato × comportamento** e sobre **lógica**. As checagens automáticas
(fmt/lint/testes) são o **piso**, não o alvo — o ponto de partida é justamente o que elas não
pegam.

## Procedimento

Siga os passos em ordem. Cada um traz o seu "porquê" para você julgar bem quando o caso real não se
encaixar exatamente no roteiro.

### 1. Delimitar o escopo

Confirme o que está sendo revisado (diff de um sprint × repo inteiro) e reúna os documentos de
contrato relevantes. Registre no relatório quais checagens automáticas já rodaram e seu status —
não para repeti-las, mas para deixar explícito que os achados abaixo são de **lógica e contrato**,
a camada que essas ferramentas não alcançam.

### 2. Ler o alvo e o contrato lado a lado

Compare o **comportamento real do código** com o que o **contrato público** (schema/README/spec/
exemplos) promete. Divergência entre o prometido e o entregue é dos achados mais graves —
especialmente quando um exemplo ou um artefato commitado no próprio repositório **expõe** a
divergência (ex.: um `exemplo.csv` commitado que o código, do jeito que está, nunca conseguiria
gerar). Contrato é rei: quando o código e o contrato discordam, ao menos um dos dois está errado, e
isso é um achado, não um detalhe.

### 3. Procurar as classes de problema que ferramentas não pegam

Ferramentas verdes provam que nada quebrou na sintaxe; não provam que a lógica está certa. Procure
ativamente:

- **Bugs de lógica e de dependência** — ordem ou dependência implícita ausente (algo que só
  funciona se outra coisa rodar antes, sem nada garantir essa ordem).
- **Falhas silenciosas** — um valor do usuário descartado sem erro (ex.: um parâmetro aceito na
  interface, mas ignorado na implementação).
- **Suposições não verificadas** — constantes "chutadas" que dependem de um fato externo não
  confirmado.
- **Colisões / efeitos globais** — estado compartilhado entre execuções que uma segunda execução
  concorrente corromperia.
- **Inconsistências entre camadas** — schema × conversor × implementação × docs contando
  histórias diferentes.

**Onde der para executar, execute.** Vários desses defeitos são *confirmáveis rodando*, e raciocinar
sobre o diff é frágil demais para eles. Uma **corrida** você exercita disparando o acesso concorrente
e observando o oversell/estado corrompido; um **parâmetro ignorado** você prova rodando o comando e
olhando a saída real; um **teste que só passa por estado prévio** você desmascara rodando-o do zero.
Um achado que você conseguiu **reproduzir** é confirmado — não uma suspeita; um que você rodou e não
reproduziu pode ser descartado. Sempre que o alvo for executável, prefira **reproduzir** ao palpite:
é a diferença entre "acho que há uma corrida aqui" e "disparei 50 reservas concorrentes de estoque
10 e 50 passaram".

### 4. Classificar cada achado por severidade

Atribua uma severidade (ex.: **alta / média / baixa**) com base no **impacto real ao usuário** e na
**probabilidade de ocorrer no uso normal** — não na facilidade de conserto. Um bug fácil de
corrigir mas que corrompe dados silenciosamente é alta; uma imperfeição cosmética e improvável é
baixa. Severidade honesta é o que permite priorizar de verdade depois.

### 5. Registrar cada achado com prova

Para cada achado, registre: **localização** (arquivo/trecho), **descrição** do problema, **cenário
de falha concreto** e **correção sugerida**. Um achado sem cenário de falha é uma suspeita, não um
achado — descreva a entrada ou o estado específico que produz o comportamento errado. Quando a
correção tiver mais de um caminho legítimo, apresente as alternativas com seus trade-offs (ex.:
"rejeitar na validação" vs. "implementar de verdade o recurso prometido") em vez de decidir
sozinho.

### 6. Registrar o que está correto

Inclua uma seção de **notas positivas**: decisões acertadas que **não devem ser alteradas**. Isso
não é elogio — é proteção. Sem registrar o que está certo, uma correção futura pode "consertar"
algo que já funcionava de propósito. Reconhecer o certo também é o que te obriga a **não inventar**
problema onde não há: se o código está correto, o relatório correto é curto.

### 7. Emitir o relatório

Produza o relatório no formato fixo abaixo. Se estiver em subagent, retorne-o como o resumo
estruturado ao contexto principal.

## Formato de saída

Use este template (os `< >` são marcadores a preencher):

```
# Code Review — <alvo>
**Escopo:** <o que foi revisado — o diff do sprint X ou o repo inteiro>
**Toolchain:** <checagens automáticas rodadas e seu status>
       — nota: os achados abaixo são de lógica/contrato, que essas ferramentas não pegam.

## Resumo
| # | Severidade | Arquivo | Problema (uma linha)       |
|---|------------|---------|----------------------------|
| 1 | Alta       | ...     | ...                        |

## Achados
### 1. <título curto do achado>
- **Arquivo(s):** <caminho e trecho>
- **Problema:** <descrição>
- **Cenário de falha:** <entrada/estado concreto → comportamento errado>
- **Correção sugerida:** <caminho, com alternativas se houver mais de um>

## Notas positivas
- <o que está correto e não deve ser alterado>

## Recomendação
- <o que priorizar e por quê>
```

Se não houver achados, diga isso claramente e entregue só as notas positivas e a recomendação — um
relatório honesto de "está bem-feito" é um resultado válido, não um fracasso.

## Princípios (o núcleo, quando o roteiro não cobrir o caso)

- **Ferramentas verdes ≠ correto** — o ponto de partida é o que `fmt`/`lint`/validação não pegam.
- **Contrato é rei** — divergência entre o prometido (schema/README/spec) e o entregue é dos
  achados mais graves.
- **Achado precisa de prova** — cada item traz um cenário de falha concreto, não uma suspeita
  vaga.
- **Reproduzir > raciocinar** — quando o alvo é executável, confirme o defeito rodando-o (corrida,
  parâmetro ignorado, teste não-reproduzível); a leitura do diff sozinha deixa passar exatamente
  esses casos.
- **Reconhecer o certo** — notas positivas protegem o que funciona de "correções" desnecessárias.
- **Severidade honesta** — priorize por impacto real e probabilidade no uso normal, não por
  facilidade de conserto.
- **Não corrigir aqui** — a skill encontra e descreve; corrigir é outra etapa.

## Fronteiras (o que esta skill NÃO faz)

- **Não corrige** os achados — apenas encontra e descreve. A correção vira sprints via `decompose`
  e é executada por `execute-sprint`.
- **Não verifica conformidade ao sprint** — julgar se o entregue corresponde ao que foi *definido*
  (escopo/restrições/entregável) é da `verify-sprint`. Esta skill julga **qualidade** (bugs,
  lógica, contrato × comportamento), não aderência ao combinado. Um código pode passar aqui e ainda
  ter desviado do que o sprint pediu — e vice-versa.
- **Não decompõe** o próprio relatório em sprints — isso é da `decompose`.
- **Não executa** sprints — é uma etapa de auditoria, não de implementação.

## Variantes por tecnologia (futuro)

A versão genérica não precisa de recursos empacotados. Se mais adiante forem criadas variantes por
stack — o que procurar especificamente em Terraform, Python, etc. —, cada uma entra como
`references/<tecnologia>.md`, lida sob demanda conforme o alvo do review. O núcleo (o raciocínio
contrato × comportamento) permanece genérico.
