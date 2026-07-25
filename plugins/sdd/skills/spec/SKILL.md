---
name: spec
description: >-
  Dispare com "/spec" e sempre que o usuário quiser definir O QUE construir antes de partir para o
  código. Use quando ele: começa a descrever um projeto, funcionalidade ou sistema novo; pede para
  levantar ou organizar requisitos ainda soltos; quer montar o escopo ou fechar o contrato do que
  será construído; quer entender bem o problema antes de implementar; recebeu requisitos vagos e
  quer transformá-los numa spec, apontando ambiguidades; ou avisa que vai mandar os requisitos aos
  poucos. Vale mesmo sem a palavra "especificação" — reconheça a intenção por trás de frases como
  "me ajuda a levantar os requisitos", "quero entender antes de codar", "monta o escopo disso". A
  skill é conversacional: confirma o entendimento passo a passo, registra decisões com o racional,
  caça lacunas e consolida um documento de especificação estável. NÃO escreve código, não planeja
  execução e não decompõe em sprints — isso é da `decompose`.
---

# spec

Esta skill transforma **requisitos brutos e conversacionais** em uma **especificação rigorosa**: um
documento que captura o que o usuário quer, confirma esse entendimento a cada passo, registra as
**decisões** tomadas (com o racional), e caça o que está **faltando** ou ambíguo — resolvendo antes de
seguir. O produto é estável o suficiente para servir de fonte à decomposição em sprints (`decompose`).

É a fase de **entender antes de fazer** do método de sprints — a primeira do fluxo em uso. Aqui não
tem código, não tem plano de execução, não tem sprint: só se **captura, confirma e consolida** o
**contrato do que será construído**. É **genérica**: raciocina sobre intenção, decisão e completude —
não sobre linguagens, frameworks ou ferramentas.

## O modo desta skill é conversacional

As outras skills do método recebem uma entrada pronta e produzem uma saída. Esta é diferente: a
entrada **chega em conversa**, muitas vezes em pedaços, e o valor está no **vaivém** — refletir de
volta, perguntar, ajustar. O maior erro que se pode cometer aqui é receber "quero construir X" e
**despejar de imediato uma especificação completa**, com decisões inventadas para preencher tudo o que
o usuário não disse. Isso troca entendimento real por uma ilusão de completude — e a decomposição
depois herda suposições que ninguém validou.

Então o ritmo padrão é **devagar e explícito**: anote o que entendeu, confirme, pergunte o que falta,
e só feche quando o usuário sinalizar. A especificação é um acordo, não um palpite.

## Pré-condições / parâmetros

- **Os requisitos do usuário** — que podem chegar **incrementalmente**, em várias mensagens. A skill
  precisa suportar "vou te mandar os requisitos aos poucos, só considere fechado quando eu avisar":
  até esse sinal, a especificação está **aberta**.
- **Nenhuma dependência de ferramenta.** Genérica por natureza — não roda nada, apenas raciocina e
  registra.

## Princípios (o núcleo do valor)

Estes seis princípios são o que separa uma boa especificação de um resumo apressado dos requisitos. O
procedimento adiante é a aplicação deles; entenda-os primeiro.

1. **Entender antes de fazer.** Nenhum código, nenhum plano de execução, nenhuma sprint nesta fase. O
   objetivo é o **contrato do que será construído** — não o *como* nem o *quando*. Se o usuário
   descreve uma solução técnica, capture-a como decisão; não comece a implementá-la.

2. **Confirmar, não presumir.** O entendimento é **refletido de volta** e validado antes de seguir —
   não acumulado como suposição silenciosa. Cada bloco de requisito recebe um "anotado: X, Y, Z"
   sucinto, para o usuário corrigir na hora. Suposição não confirmada é dívida que vence na
   decomposição.

3. **Decisão registrada é decisão rastreável.** Cada escolha relevante vira uma **decisão anotada, com
   o porquê**. Quando há alternativas, apresente os trade-offs e deixe o usuário decidir; se ele
   delegar ("escolhe você"), escolha um **default sensato e registre-o como decisão** — explícito, com
   o racional. O que não pode acontecer é uma escolha entrar na spec sem ninguém saber que foi feita.

4. **Incremental por padrão.** A especificação **não fecha até o usuário sinalizar**. Requisitos podem
   chegar em blocos; a skill anota cada um e confirma, mas **não declara "pronto"** por conta própria
   enquanto o usuário estiver alimentando. Fechar cedo é o mesmo erro de despejar a spec completa — só
   distribuído no tempo.

5. **Lacuna é risco.** Ambiguidades são **caçadas ativamente**, não descobertas depois. Pergunte
   proativamente sobre casos de borda, formatos de entrada/saída, restrições, estado (backend,
   persistência), ambientes, e o que não foi dito. O que fica em aberto ou vira **pergunta** ou vira
   **default explícito registrado como decisão** — nunca um buraco silencioso.

6. **Genérica.** Sem ferramentas ou stacks embutidas. A spec raciocina sobre intenção e contrato; o
   *como* técnico é decisão do projeto, não desta skill.

## Procedimento

Siga os passos em ordem. Cada um traz o seu "porquê" para você julgar bem quando o caso real não se
encaixar no roteiro.

### 1. Capturar a intenção de forma incremental

Aceite requisitos em **várias mensagens**. A cada bloco, registre o que entendeu de forma sucinta e
explícita — **"anotado: X, Y, Z"** — para o usuário ver e corrigir. **Não** trate a especificação como
completa até o usuário sinalizar. Se ele disse "vou mandar aos poucos", leve isso a sério: continue
anotando e confirmando, sem tentar fechar. A pressa de consolidar cedo é o que faz a spec ficar cheia
de suposições.

### 2. Confirmar o entendimento passo a passo

Reflita de volta o que entendeu e **deixe o usuário corrigir antes de prosseguir**. Isso não é
formalidade: é onde os mal-entendidos aparecem enquanto ainda são baratos de arrumar. Prefira
confirmar em pedaços curtos ("então o filtro é por período, e o período é inclusivo nas duas pontas —
certo?") a acumular um bloco grande de suposições e pedir validação só no fim.

### 3. Registrar as decisões com o racional

Cada escolha relevante vira uma **decisão anotada com o porquê**. Quando houver alternativas reais,
apresente os **trade-offs** e deixe o usuário escolher. Se ele delegar, escolha um **default sensato**
e **registre-o como decisão explícita** — dizendo que foi um default assumido e por quê, para que fique
fácil de rever depois. A regra é: nada de escolha invisível. Uma decisão que não está escrita, com
razão, é uma decisão que a decomposição vai tomar de novo — provavelmente diferente.

### 4. Caçar lacunas e ambiguidades

Procure ativamente o que **não** foi dito: casos de borda, formatos de entrada e saída, restrições,
onde mora o estado (backend, persistência, arquivo), ambientes, volumes, o que acontece no erro.

Vá além do que o usuário listou e cace as **obrigações universais do domínio** — as que quase nenhum
requisito bruto escreve, mas que todo sistema daquele tipo tem de cumprir para não ser perigoso ou
incorreto: **segurança** (segredos e senhas nunca em texto claro), **concorrência** (acesso
simultâneo seguro — sem corrida, sem oversell), **integridade de estado** (operações atômicas e
idempotentes; nada corrompido por uma reexecução ou uma sequência inesperada), **conservação** (em
dinheiro/estoque, nada some nem duplica; sem saldo negativo). Traga cada uma que se aplica como
**pergunta** ou como **default registrado como decisão** — nunca a deixe implícita. Um invariante que
a spec não nomeia é um invariante que ninguém vai testar depois (e que a `decompose` não terá como
transformar em entregável).

Quando puder **resolver ou propor** algo, faça — endereçe o que der antes de pedir esclarecimento. Para
o que sobrar, faça **no máximo uma pergunta por vez** quando possível (uma pergunta focada é mais fácil
de responder que um questionário), e para o que ficar em aberto, **proponha um default e marque como
decisão**. Uma lacuna tratada agora é um retrabalho evitado depois.

### 5. Confirmar a completude ativamente

Antes de consolidar, **cheque o que pode estar faltando e pergunte** — não declare "pronto" pela
sensação. "Acho que cobrimos parsing, filtro e saída; falta dizer o que fazer com uma linha malformada
e onde o arquivo de saída é gravado — quer definir agora ou deixo um default?" é melhor que fechar em
silêncio e descobrir o buraco na decomposição. E respeite o sinal do usuário: se ele disse que ainda
vai mandar coisas, a completude não é sua para declarar.

### 6. Consolidar a especificação

Quando o usuário sinalizar que fechou (ou confirmar que pode consolidar), produza o **documento
estruturado** no formato abaixo. É esse documento que a `decompose` consome — então ele precisa ser
autossuficiente: quem for decompor não vai reabrir a conversa, vai ler a spec.

## Formato de saída (documento de especificação)

Use este template (os `< >` são marcadores a preencher). O esqueleto vazio também está em
[`assets/spec-template.md`](assets/spec-template.md) para copiar. Contém, no mínimo:

```
# Especificação — <projeto / funcionalidade>

## Visão geral
<o que é, para quem, qual problema resolve — em poucas frases>

## Requisitos
### Funcionais
- <o que o sistema faz — explícito, verificável>
### Não-funcionais
- <desempenho, restrições operacionais, limites — quando houver>

## Decisões (com racional)
| # | Decisão | Racional | Origem |
|---|---------|----------|--------|
| 1 | <a escolha feita> | <por quê> | <usuário | default assumido> |

## Contrato / interface  <quando aplicável>
- <formatos de entrada e saída, o que é público, assinaturas — quando houver interface>

## Restrições e não-objetivos
- <o que está fora de escopo, o que NÃO se pretende fazer>

## Pontos em aberto
- <o que ainda precisa de decisão, se houver — cada um com o que falta para resolver>
```

Notas sobre o preenchimento:

- **Decisões** é o coração do documento. Todo default assumido (seção anterior) aparece aqui, marcado
  como tal na coluna *Origem* — é o que torna uma suposição rastreável em vez de invisível.
- **Contrato/interface** só entra quando faz sentido (há uma API, um formato de arquivo, um schema).
  Não force a seção quando o projeto não tem interface pública.
- **Pontos em aberto** é um resultado **válido**: uma spec pode fechar com itens ainda por decidir,
  desde que estejam **nomeados** e não escondidos. É melhor uma lacuna declarada que um buraco
  silencioso — a `decompose` sabe lidar com o que está marcado como aberto, não com o que ninguém viu.

## Fronteiras (o que esta skill NÃO faz)

- **Não decompõe em sprints** — isso é da `decompose`, que consome a saída desta. Aqui não se corta
  nem se sequencia trabalho.
- **Não implementa nada** — nenhum código, nenhum arquivo de solução. Se o usuário empurrar para "já
  começa a codar", mantenha o foco em especificar; registre a intenção técnica como decisão para a
  fase seguinte, mas não a execute.
- **Não faz plano de execução** — o *como* e o *quando* são de outras camadas. Esta skill entrega o
  **contrato do que**, não o roteiro do como.
- É a etapa de **entendimento**, anterior a tudo. Seu único produto é a especificação.

## Variantes por tecnologia (futuro)

A especificação é agnóstica de tecnologia por decisão: capturar intenção, decisão e completude não muda
entre um projeto de dados, uma API ou uma migração. Não há variantes de stack previstas. Se algum dia
surgir necessidade de um guia específico (ex.: o que costuma virar lacuna em tal domínio), ele entra
como `references/<tema>.md`, lido sob demanda — o núcleo permanece genérico.
