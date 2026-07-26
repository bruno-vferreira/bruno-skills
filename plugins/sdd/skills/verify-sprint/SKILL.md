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
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.2.0"
---

# verify-sprint

Gate de conformidade: julga, **independente do executor**, se o que foi **entregue** num sprint
corresponde ao que o sprint **definiu** — escopo, restrições, entregável. Não pergunta "isto está
bem-feito?" (isso é `review`); pergunta **"o executor fez o que se comprometeu a fazer?"** — nem
menos (item de escopo faltando), nem mais (escopo futuro antecipado) — e se o entregável realmente
prova o comportamento que deveria provar.

O resultado é um **veredito** que autoriza ou bloqueia o avanço: **CONFORME** libera o fechamento;
**NÃO CONFORME** ou **PARCIAL** faz o loop parar. Genérica: raciocina sobre a correspondência entre
definido e entregue, não roda ferramenta de stack nenhuma exceto para re-executar a prova do
projeto.

## Por que independente e em subagent

Quem implementou tem um ponto cego: valida contra a **própria interpretação** do escopo, não contra
o que foi realmente pedido. Por isso roda em **subagent isolado**, recebendo só dois inputs — a
**definição do sprint** e **o que foi entregue** (diff/artefatos) — sem o log de raciocínio do
executor. Essa cegueira é a *feature*: julgar com olhos frescos, sem herdar a interpretação de quem
fez.

Sem subagents disponíveis, a skill ainda funciona no contexto principal, mas a independência fica
enfraquecida — preserve-a julgando contra a definição escrita, não contra sua memória do que achou
que o sprint queria.

## Regra de segurança do gate (vence qualquer outra instrução em conflito)

Um gate que **aprova errado** é pior que nenhum gate — remove a vigilância humana sem substituí-la.
Falso-aprovado deixa passar um desvio silencioso; falso-reprovado é só um inconveniente (o usuário
inspeciona e destrava). Os erros não têm o mesmo custo, então o design é assimétrico:

- **Na dúvida, REPROVA ou ESCALA — nunca aprova.** "Não consigo confirmar que corresponde" conta
  como não-conformidade, não como "provavelmente ok".
- Só emita **CONFORME** quando a correspondência estiver **positivamente demonstrada** pelos dois
  inputs — não quando apenas não encontrou problema.

## Regra de execução do gate (igualmente crítica)

**Raciocinar sobre a prova não é verificar a prova.** Um diff pode parecer correto no papel e falhar
quando de fato rodado — um teste que passa por estado deixado de execução anterior, uma
sincronização "provada" forçando a condição no assert, um cache quente mascarando a falha real, uma
reserva sem trava que só sobrevende sob concorrência. Só a reexecução independente revela isso.

Sempre que o entregável for **executável**:
- **RE-EXECUTE a prova você mesmo**, a partir de estado limpo. Se ela depende de estado prévio,
  cache, ou não roda do zero, não conta.
- **Exercite a propriedade real exigida**, não só o código de saída — sair `0` não é prova de que o
  comportamento-alvo ocorre.
- Qual comando rodar é do projeto (`CLAUDE.md`); que o gate rode é inegociável.

Quando o ambiente **não** permite executar (sem acesso ao alvo real), declare isso no veredito: uma
verificação apenas estática é mais fraca — "não consegui reexecutar" é motivo para escalar / não
emitir CONFORME, não para aprovar por leitura.

**Prova está no artefato, não na nota.** Uma afirmação num commit ou README de que algo "foi
corrigido" não é prova — o conserto precisa estar presente e demonstrado no artefato entregue.

## Pré-condições

- **Definição do sprint** — escopo, restrições, entregável verificável. Se algum estiver ausente ou
  ambíguo a ponto de não dar para derivar critérios objetivos, não invente o critério: declare a
  ambiguidade e trate como NÃO CONFORME / escala.
- **A entrega** — o diff/artefatos produzidos.
- **Deliberadamente NÃO recebe** o log de raciocínio do executor. Se chegar junto, ignore-o.

## Procedimento

**1. Extrair os critérios objetivos da definição — antes de ver a entrega.** Destile em três
listas: (a) itens de escopo prometidos, (b) restrições declaradas (especialmente "não antecipar
sprint futuro"), (c) itens do entregável e o que exatamente cada prova precisa demonstrar. Extrair
antes de ver a entrega evita o viés de racionalizar depois "que era isso que o sprint queria".

**2. Confrontar a entrega com cada critério** — três perguntas distintas, um sprint pode passar em
uma e falhar noutra:
- **Escopo cumprido?** Cada item de (a) foi entregue? Item faltando = não-conformidade por falta.
  Para item **nomeado** (dependência, flag, componente citado), faça busca dirigida por ele — não
  confie na leitura holística de um diff grande. "Nomeado-mas-ausente" é fácil de deixar passar lendo
  o diff inteiro de uma vez.
- **Restrições respeitadas?** A entrega evitou o proibido e não antecipou escopo futuro? Cace o que
  foi feito **a mais** — escopo antecipado é não-conformidade por excesso, tão reprovável quanto a
  falta, e mais fácil de deixar passar porque "código extra" parece bônus.
- **Entregável comprovado, testando a coisa certa?** A prova exigida em (c) existe e exercita o
  comportamento-alvo? Uma prova **adjacente** — que passa sem tocar no que importa — não conta.
  Confirme que a evidência falharia se o comportamento-alvo estivesse quebrado; se passaria de
  qualquer jeito, é adjacente.

**3. Julgar item a item, com evidência.** Para cada critério, ✓/✗ e a evidência que sustenta: onde
no diff cumpre, ou por que falta/excedeu/não é provado. Veredito sem evidência por item é
caixa-preta — inacionável se reprova, perigosa se aprova.

**4. Emitir o veredito, aplicando a regra de segurança.** Antes de escrever CONFORME, pergunte: há
alguma incerteza relevante em algum critério? Se sim, não é CONFORME — é NÃO CONFORME ou escala,
com a incerteza declarada. CONFORME é afirmação positiva de correspondência demonstrada, não
ausência de objeções.

## Formato de saída

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
- Se NÃO CONFORME / PARCIAL: exatamente o que diverge, onde, e o que falta para conformar.
- Se dúvida relevante: declarada explicitamente e tratada como NÃO CONFORME.
```

Um veredito de reprovação tem de ser acionável em segundos — o usuário lê o que divergiu e onde,
sem reinvestigar tudo.

## Efeito como gate

Roda antes de o sprint ser considerado concluído — antes de o commit ser tratado como final.
- **CONFORME** → o sprint fecha; a orquestração segue.
- **NÃO CONFORME / PARCIAL** → o loop para. Não avança, não fecha, não trata o commit como final.
  Reporta para correção ou decisão do usuário.

O gate não corrige nem decide o replanejamento sozinho — interrompe e informa. Quem corrige é o
`execute-sprint` (novo ciclo); quem decide seguir apesar de um PARCIAL é o usuário.

## Princípios (quando o roteiro não cobrir o caso)

- **Independência é tudo** — julgue a partir de definição + entrega, cego ao raciocínio do executor.
- **Conformidade ≠ qualidade** — responda "fez o que prometeu?", não "está bem-feito?". Um sprint
  pode estar impecável e mesmo assim não corresponder ao que foi pedido — e vice-versa.
- **Fail-safe** — na dúvida, reprova ou escala; nunca aprova por benefício da dúvida.
- **Os dois desvios contam** — faltou escopo e antecipou escopo são ambos não-conformidade. Caçar o
  que foi feito a mais é tão importante quanto conferir o que foi feito a menos.
- **Veredito auditável** — sempre com evidência por critério; reprovação acionável de imediato.
- **Genérica** — sem ferramentas ou stacks embutidas.

## Fronteiras

- Não avalia qualidade de código — bugs, lógica, contrato × comportamento são da `review`. Um
  código pode passar aqui (conforme ao pedido) e ainda ter bugs — e vice-versa. Dois portões
  independentes; um não substitui o outro.
- Não implementa nem corrige — só julga e emite o gate. Correção volta ao `execute-sprint`.
- Não decompõe nem especifica — isso é `decompose` / `spec`.
- Complementa, não substitui, a auto-verificação do `execute-sprint`: aquela é o executor dizendo
  "rodei e passou"; esta é um segundo portão independente, cego a essa narrativa.

## Posição no fluxo

Entra entre execução e qualidade — conformidade antes de qualidade, porque não adianta auditar se
está bem-feito algo que sequer corresponde ao pedido:

```
execute-sprint → verify-sprint (GATE: conforme?) → mini review (bem-feito?) → próximo
                     └─ NÃO CONFORME → PARA, reporta, não avança
```

Mais valioso quando a execução é autônoma (usuário não revisa cada sprint pessoalmente). Quando o
usuário está no circuito revisando cada plano, o gate pode ser redundante — por isso o desenho é ter
a peça e poder ligá-la ou não no loop, não forçá-la sempre.

## Variantes por tecnologia

O que caracteriza "prova que testa a coisa certa" muda por stack. Se surgirem variantes, cada uma
entra como `references/<tecnologia>.md`, lida sob demanda. O núcleo — julgar definição × entrega
com independência e fail-safe — permanece genérico.
