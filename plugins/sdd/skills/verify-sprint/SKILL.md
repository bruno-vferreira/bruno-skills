---
name: verify-sprint
description: >-
  Use ao terminar de implementar um sprint (ou fase/etapa de roadmap) e ANTES de fechá-lo,
  commitá-lo ou deixar a orquestração avançar — para conferir, independente do executor, se a
  entrega bate com o que o sprint DEFINIU: escopo cumprido, restrições respeitadas (nada de escopo
  futuro antecipado nem "coisa a mais" do combinado) e entregável de fato comprovado. É um GATE:
  emite CONFORME / NÃO CONFORME / PARCIAL e bloqueia o avanço se a entrega desviou; na dúvida,
  reprova. Dispare por "/verify-sprint", como portão automático no loop de sprints, ou quando
  pedirem "valida se a entrega corresponde à definição do sprint", "o sprint fez o que prometeu?",
  "posso fechar/commitar isto?", ou "quero um segundo portão independente sobre
  escopo/restrições/entregável". NÃO é code review (bugs/lógica), NÃO valida deploy nem o plano do
  sprint, NÃO corrige — só julga aderência ao combinado, em qualquer domínio.
---

# verify-sprint

Esta skill é um **gate de conformidade**. Ela julga, de forma **independente do executor**, se o que
foi **entregue** em um sprint corresponde ao que o sprint **definiu** — escopo, restrições e
entregável. Não pergunta "isto está bem-feito?" (isso é a `review`); pergunta **"o executor fez o que
se comprometeu a fazer?"** — nem menos (faltou um item do escopo), nem mais (antecipou escopo futuro,
violando as restrições) — e se o entregável realmente prova o comportamento que deveria provar.

O resultado é um **veredito** que **autoriza ou bloqueia** o avanço do sprint: **CONFORME** libera o
fechamento; **NÃO CONFORME** ou **PARCIAL** faz o loop **parar**. É **genérica**: não conhece stacks
nem roda ferramentas — raciocina sobre a correspondência entre o **definido** e o **entregue**.

## Por que independente e em subagent (o ponto central)

Quem implementou o sprint tem um **ponto cego**: valida contra a **própria interpretação** do escopo,
não contra o que o sprint realmente pediu. Auto-avaliação tem viés estrutural — é fácil convencer-se
de que "foi isto que o sprint queria" quando foi isto que se acabou de fazer. Por isso `verify-sprint`
roda em um **subagent isolado** que recebe apenas **dois inputs**:

1. a **definição do sprint** (escopo, restrições, entregável), e
2. **o que foi entregue** (o diff / os artefatos do sprint).

O subagent **não vê o log de raciocínio do executor** — essa cegueira é a *feature*, não uma
limitação. Ele julga a correspondência entre o prometido e o entregue **com olhos frescos**, sem
herdar a interpretação de quem fez. É o que torna o gate genuinamente independente: o mesmo princípio
de isolamento da `review`, aplicado a **conformidade** em vez de **qualidade**.

Se o ambiente não tiver subagents, a skill ainda funciona no contexto principal — mas a independência
fica enfraquecida. Preserve-a ativamente: julgue contra a **definição escrita**, não contra a memória
do que você achou que o sprint queria. Em subagent, retorne apenas o veredito estruturado ao contexto
principal.

## Regra de segurança do gate (crítica — leia antes de tudo)

Um gate que **aprova errado** é **pior que nenhum gate**: ele remove a vigilância humana (o usuário
para de conferir *porque confia no gate*) sem substituí-la de fato. Um falso-aprovado deixa passar um
desvio silencioso; um falso-reprovado é apenas um inconveniente (o usuário inspeciona e destrava).
Como os dois erros não têm o mesmo custo, o design é **assimétrico de propósito**:

- **Na dúvida, REPROVA ou ESCALA — nunca aprova.** "Não consigo confirmar que corresponde" é tratado
  como **não-conformidade**, não como "provavelmente ok". O benefício da dúvida vai para a segurança,
  jamais para o avanço.
- **Falso-aprovado é o pior erro possível.** Prefira reprovar demais a aprovar de menos. Só emita
  **CONFORME** quando a correspondência estiver **positivamente demonstrada** pelos dois inputs — não
  quando apenas *não encontrou* um problema.

Esta regra vence qualquer outra instrução desta skill quando houver conflito.

## Regra de execução do gate (tão crítica quanto a de segurança)

**Raciocinar sobre a prova NÃO é verificar a prova.** Ler um diff e concluir "esta prova parece
válida e reproduzível" é frágil — uma prova pode *parecer* correta no papel e **falhar quando de
fato rodada**: um teste que passa por causa de estado deixado de uma execução anterior; uma
sincronização "provada" por um comando que força a condição no instante do assert; um cache quente
que mascara a falha real; uma reserva sem trava que só sobrevende sob concorrência. Nesses casos, só
a **reexecução independente** revela a verdade — e é exatamente aí que mora o maior valor do gate.

Por isso, sempre que o entregável for **executável**:

- **RE-EXECUTE a prova você mesmo**, do seu jeito, **a partir de um estado limpo** — não confie no
  verde relatado pelo executor nem no seu próprio raciocínio sobre o diff. Se a prova depende de
  estado prévio, de cache, do mesmo processo, ou não roda do zero, ela **não conta**.
- **Exercite a propriedade REAL exigida**, não só o código de saída. Sair `0` não é prova de que o
  comportamento-alvo ocorre (ver passo 2c, prova adjacente).
- Isto é **genérico quanto à stack**: *qual* comando rodar é do projeto (`CLAUDE.md` /
  `references/<tecnologia>.md`); *que o gate rode* é inegociável.

Quando o ambiente **não** permite executar (sem acesso ao alvo real — ex.: infra que exige um
cluster vivo), **declare isso no veredito**: uma verificação apenas estática é mais fraca, e "não
consegui reexecutar a prova de forma independente" é motivo para **escalar / não emitir CONFORME** —
não para aprovar por leitura.

**Prova está no artefato, não na nota.** Uma afirmação — num commit, num README, num relato do
executor — de que algo "foi corrigido", "foi revertido" ou "passa" **não é prova**. A correção tem
de estar **presente e demonstrada no artefato entregue** (o diff / o estado do repositório). Se o
conserto só existe como promessa e não como código verificável, o veredito **não é** CONFORME.

## Pré-condições / inputs

- **Definição do sprint** — o escopo (o que fazer), as restrições (o que **não** fazer / não
  antecipar) e o **entregável verificável** (a prova que o sprint exige). Se qualquer um dos três
  estiver ausente ou ambíguo a ponto de você não conseguir derivar critérios objetivos, **não invente
  o critério**: isso é ambiguidade genuína — declare-a e trate como **NÃO CONFORME / escala** (regra
  de segurança). Um gate não pode certificar conformidade contra um alvo que ele mesmo teve de
  adivinhar.
- **A entrega** — o diff / os artefatos produzidos no sprint (o que mudou).
- **Deliberadamente NÃO recebe** o log de raciocínio do executor — para preservar a independência de
  julgamento (ver seção acima). Se essa informação chegar junto, **ignore-a**: julgue definição ×
  entrega, não a narrativa de quem implementou.

A skill é **genérica quanto à stack** (não embute ferramentas de nenhuma tecnologia), mas **não é
passiva**: quando o entregável é executável, ela **re-executa a prova de forma independente** (ver a
regra de execução acima), usando o comando que o projeto define. Só quando não há alvo executável é
que ela se limita a julgar a correspondência definição × entrega de forma estática — e, nesse caso,
declara a limitação no veredito.

## Procedimento

Siga os passos em ordem. Cada um traz o seu "porquê" para você julgar bem quando o caso real não se
encaixar exatamente no roteiro.

### 1. Extrair os critérios objetivos da definição

Leia a definição do sprint e destile-a em três listas explícitas, **antes** de olhar a entrega:

- **(a) Itens de escopo** prometidos — o que o sprint disse que ia entregar.
- **(b) Restrições** declaradas — o que era proibido fazer, e em especial o que era "não antecipar /
  sprint futuro".
- **(c) Itens do entregável** verificável — qual prova o sprint exige, e **o que exatamente** essa
  prova precisa demonstrar (o comportamento-alvo).

Extrair os critérios **antes** de ver a entrega evita o viés de "ler o que foi feito e depois racionalizar
que era isso que o sprint queria". O alvo se fixa a partir da definição, não da entrega.

### 2. Confrontar a entrega com cada critério

Examine o diff / os artefatos contra as três listas. São **três perguntas distintas** — responda cada
uma separadamente, porque um sprint pode passar em uma e falhar em outra:

- **Escopo cumprido?** Cada item prometido em (a) foi de fato entregue? Um item que ficou de fora é
  **não-conformidade por falta** — aponte exatamente qual. Para cada item **nomeado** no escopo (uma
  dependência, uma flag, um componente citado pelo nome), faça uma **busca dirigida por ele** na
  entrega — não confie na leitura holística de um diff grande. "Nomeado-mas-ausente" (o escopo pede
  `X` e `X` simplesmente não aparece no diff) é um modo de falha barato de mecanizar e fácil de
  deixar passar quando se lê o diff inteiro de uma vez.
- **Restrições respeitadas?** A entrega evitou o que era proibido **e não antecipou** escopo de
  sprints futuros? Aqui não basta olhar o que foi feito; é preciso caçar o que foi feito **a mais**.
  Escopo antecipado é **não-conformidade por excesso** — igualmente reprovável, e mais fácil de deixar
  passar porque "código extra" parece bônus, não defeito. Não é: quebra o contrato do sprint, entrega
  algo que ninguém revisou naquele contexto e mistura mudanças que deveriam ser fatiadas.
- **Entregável comprovado — e testando a coisa certa?** A prova exigida em (c) existe **e** exercita o
  comportamento-alvo? Uma **prova adjacente** — que passa sem tocar no que importa (ex.: um teste que
  cobre o caso trivial mas nunca aciona a lógica que o sprint pedia para provar) — **não conta**. Uma
  prova que não testa o alvo é indistinguível de não ter prova nenhuma. Confirme que a evidência
  *falharia* se o comportamento-alvo estivesse quebrado; se ela passaria de qualquer jeito, é
  adjacente.

### 3. Julgar item a item, com evidência

Para **cada** critério, registre um julgamento (✓ / ✗) **e a evidência** que o sustenta: onde no diff
o item está cumprido, ou por que está faltando / foi excedido / não é provado pela evidência
apresentada. Um veredito sem evidência por item é uma caixa-preta — e uma caixa-preta que reprova é
inacionável, uma que aprova é perigosa.

### 4. Emitir o veredito, aplicando a regra de segurança

Consolide os julgamentos no veredito (formato abaixo). Antes de escrever **CONFORME**, faça a
verificação final da regra de segurança: **há alguma incerteza relevante** em algum critério? Se sim,
o veredito **não é** CONFORME — é NÃO CONFORME (ou escala), com a incerteza declarada explicitamente.
CONFORME é uma afirmação positiva de correspondência demonstrada, não a ausência de objeções.

## Formato de saída (veredito auditável)

O veredito **nunca** é um binário nu; vem sempre com evidência acionável por critério. Use este
template (os `< >` são marcadores a preencher):

```
# Verificação de Conformidade — Sprint <id/nome>
**Veredito:** CONFORME | NÃO CONFORME | CONFORME PARCIALMENTE

## Escopo
- [✓/✗] <item prometido> — evidência: <onde no diff cumpre / por que falta>

## Restrições
- [✓/✗] <restrição> — respeitada? antecipou escopo futuro? evidência: <onde>

## Entregável
- [✓/✗] <item do entregável> — a prova existe e exercita o comportamento-alvo? evidência: <onde;
  por que a prova de fato testa o alvo, ou por que é adjacente>

## Conclusão do gate
- Se CONFORME: uma linha confirmando que os três eixos correspondem ao definido.
- Se NÃO CONFORME / PARCIAL: exatamente **o que** diverge, **onde**, e **o que falta** para conformar.
- Se dúvida relevante: declarada explicitamente e tratada como NÃO CONFORME (regra de segurança).
```

Um veredito de reprovação tem de ser **acionável em segundos**: o usuário lê *o que* divergiu e *onde*,
sem ter de reinvestigar tudo. Se você reprovou, o próximo passo de correção deve saltar do texto.

## Efeito como gate (o que "bloquear" significa)

Roda **antes de o sprint ser considerado concluído** — idealmente antes de o commit do sprint ser
tratado como final, para não deixar um commit "aprovado" que na verdade desviou.

- **CONFORME** → o sprint pode fechar; a orquestração segue (para o mini review / próximo sprint).
- **NÃO CONFORME / PARCIAL** → o loop **para**. Não avança, não fecha o sprint, não trata o commit
  como final. Reporta o veredito para correção — ou para decisão do usuário.

O gate não corrige e não decide sozinho o replanejamento: ele **interrompe** e **informa**. Quem
corrige é o `execute-sprint` (num novo ciclo); quem decide seguir apesar de um PARCIAL é o usuário.

## Princípios (o núcleo, quando o roteiro não cobrir o caso)

- **Independência é tudo** — julgue a partir de definição + entrega, cego ao raciocínio do executor.
- **Conformidade ≠ qualidade** — responda "fez o que prometeu?", não "está bem-feito?". Um sprint pode
  estar impecável e mesmo assim **não corresponder** ao que foi pedido — e vice-versa.
- **Fail-safe** — na dúvida, reprova ou escala; nunca aprova por benefício da dúvida. Falso-aprovado é
  o pior erro.
- **Os dois desvios contam** — faltou escopo **e** antecipou escopo são ambos não-conformidade. Caçar
  o que foi feito a mais é tão importante quanto conferir o que foi feito a menos.
- **A prova tem de testar a coisa certa** — prova adjacente que passa sem exercitar o alvo é
  não-conformidade, não "quase lá".
- **Re-executar, não raciocinar** — se o entregável é executável, rode a prova você mesmo, do estado
  limpo; raciocinar sobre o diff não substitui rodá-lo. Sem poder executar, escale.
- **Prova no artefato, não na nota** — "foi corrigido/revertido" dito em commit ou README não conta;
  a correção tem de estar presente e demonstrada no artefato entregue.
- **Veredito auditável** — sempre com evidência por critério; reprovação acionável de imediato.
- **Genérica** — sem ferramentas ou stacks embutidas.

## Fronteiras (o que esta skill NÃO faz)

- **Não avalia qualidade de código** — bugs, lógica, contrato × comportamento são da `review`. Aqui é
  só aderência ao **definido**. Um código pode passar aqui (conforme ao pedido) e ainda ter bugs — e
  passar na `review` (bem-feito) e ainda ter desviado do escopo. São dois portões independentes, de
  ângulos diferentes; um não substitui o outro.
- **Não implementa nem corrige** — apenas julga a conformidade e emite o gate. A correção volta para o
  `execute-sprint`.
- **Não decompõe nem especifica** — isso é da `decompose` / `spec`.
- **Complementa, não substitui**, a auto-verificação do `execute-sprint`: aquela é o executor dizendo
  "rodei a prova e passou"; esta é um **segundo portão independente**, cego a essa narrativa.

## Posição no fluxo (para a orquestração)

No loop das skills de orquestração, o gate entra **entre execução e qualidade** — conformidade
**antes** de qualidade, porque não adianta auditar se está bem-feito algo que sequer corresponde ao que
foi pedido:

```
execute-sprint  →  verify-sprint (GATE: conforme?)  →  mini review (bem-feito?)  →  próximo
                        │
                        └─ NÃO CONFORME → PARA, reporta, não avança
```

O gate é mais valioso quando a execução é **autônoma** (o usuário não revisa cada sprint pessoalmente)
— ele automatiza o julgamento de conformidade que, de outro modo, seria humano. Quando o usuário
**está** no circuito revisando cada plano, o gate pode ser redundante; por isso o desenho recomendado
é **ter a peça e poder ligá-la ou não** no loop, não forçá-la sempre.

## Variantes por tecnologia (futuro)

A versão genérica não precisa de recursos empacotados. O que caracteriza "prova que testa a coisa
certa" muda por stack (o que é um teste que de fato exercita o alvo em Terraform, em Python, em uma
migração de dados…). Se essas variantes forem criadas, cada uma entra como `references/<tecnologia>.md`,
lida sob demanda. O núcleo — julgar definição × entrega com independência e fail-safe — permanece
genérico.
