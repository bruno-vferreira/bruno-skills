---
name: verify-sprint
description: >-
  Gate de conformidade independente sobre um sprint entregue: confere se a entrega bate com o que
  o sprint DEFINIU — escopo cumprido, restrições respeitadas (nada de escopo futuro antecipado) e
  entregável de fato comprovado — e emite CONFORME / PARCIAL / NÃO CONFORME, bloqueando o avanço
  se a entrega desviou; na dúvida, reprova. Use ao terminar de implementar um sprint (ou
  fase/etapa de roadmap) e ANTES de fechá-lo ou commitá-lo, como portão automático no loop de
  sprints, ou quando pedirem "o sprint fez o que prometeu?", "valida a entrega contra a definição",
  "posso fechar/commitar isto?". Dispare também por "/verify-sprint". Não é code review
  (bugs/lógica são da `review-quality`) e não corrige — só julga aderência ao combinado, em qualquer
  domínio.
argument-hint: "[sprint]"
context: fork
background: false
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.4.0"
---

# verify-sprint

Gate de conformidade: julga, **independente do executor**, se o que foi **entregue** num sprint
corresponde ao que o sprint **definiu** — escopo, restrições, entregável. Não pergunta "isto está
bem-feito?" (isso é `review-quality`); pergunta **"o executor fez o que se comprometeu a fazer?"** — nem
menos (item de escopo faltando), nem mais (escopo futuro antecipado) — e se o entregável realmente
prova o comportamento que deveria provar.

O resultado é um **veredito** que autoriza ou bloqueia o avanço: **CONFORME** libera o fechamento;
**NÃO CONFORME** ou **PARCIAL** faz o loop parar. Genérica: raciocina sobre a correspondência entre
definido e entregue, não roda ferramenta de stack nenhuma exceto para re-executar a prova do
projeto.

## Por que independente

Quem implementou tem um ponto cego: valida contra a **própria interpretação** do escopo, não contra
o que foi realmente pedido. Por isso esta skill roda em **subagent isolado** (`context: fork` no
frontmatter), recebendo só dois inputs — a **definição do sprint** e **a entrega** (diff/artefatos)
— sem o histórico da conversa nem o raciocínio do executor. Essa cegueira é a *feature*: julgar com
olhos frescos, sem herdar a interpretação de quem fez. Num runtime sem suporte a fork, preserve-a
julgando contra a definição escrita, não contra memória da conversa.

## Regras do gate (vencem qualquer outra instrução em conflito)

Um gate que **aprova errado** é pior que nenhum gate — remove a vigilância humana sem substituí-la.
Falso-aprovado deixa passar um desvio silencioso; falso-reprovado é só um inconveniente (o usuário
inspeciona e destrava). Os erros não têm o mesmo custo, então o design é assimétrico e a verificação
é sempre re-executada, nunca só lida:

- **Na dúvida, REPROVA ou ESCALA — nunca aprova.** "Não consigo confirmar que corresponde" conta
  como não-conformidade. Só emita **CONFORME** quando a correspondência estiver **positivamente
  demonstrada** pelos dois inputs — não quando apenas não encontrou problema.
- **Raciocinar sobre a prova não é verificar a prova.** Um diff pode parecer correto no papel e
  falhar quando de fato rodado — um teste que passa por estado deixado de execução anterior, uma
  sincronização "provada" forçando a condição no assert, uma reserva sem trava que só sobrevende sob
  concorrência. Sempre que o entregável for **executável**, **RE-EXECUTE a prova você mesmo**, a
  partir de estado limpo — se depende de cache ou estado prévio, não conta — e **exercite a
  propriedade real exigida**, não só o código de saída (sair `0` não é prova). Qual comando rodar é
  do projeto (`CLAUDE.md`); que o gate rode é inegociável.
- Quando o ambiente **não** permite executar, declare isso no veredito — verificação só estática é
  motivo para escalar / não emitir CONFORME, nunca para aprovar por leitura.
- **Prova está no artefato, não na nota.** Uma afirmação num commit ou README de que algo "foi
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
alguma incerteza relevante em algum critério? Se sim, não é CONFORME — reprove com a incerteza
declarada. CONFORME é afirmação positiva de correspondência demonstrada, não ausência de objeções.
Entre os vereditos de reprovação: **PARCIAL** quando a maioria dos critérios está positivamente
demonstrada e o que falta é enumerável item a item; **NÃO CONFORME** quando o desvio é central ou a
incerteza é difusa. Ambos bloqueiam o avanço — a diferença está no retrabalho comunicado, não no
efeito do gate.

## Formato de saída

Use exatamente este template:

```
# Verificação de Conformidade — Sprint <id/nome>
**Veredito:** CONFORME | PARCIAL | NÃO CONFORME

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

## Fronteiras

- Não avalia qualidade de código — bugs, lógica, contrato × comportamento são da `review-quality`.
  Um
  código pode passar aqui (conforme ao pedido) e ainda ter bugs — e vice-versa. Dois portões
  independentes; um não substitui o outro.
- Não implementa nem corrige — só julga e emite o gate. Correção volta ao `execute-sprint`.
- Não decompõe nem especifica — isso é `decompose` / `spec`.
- Complementa, não substitui, a auto-verificação do `execute-sprint`: aquela é o executor dizendo
  "rodei e passou"; esta é um segundo portão independente, cego a essa narrativa.

## Posição no fluxo

Entra entre execução e qualidade — conformidade antes de qualidade, porque não adianta auditar se
está bem-feito algo que sequer corresponde ao pedido, e roda antes de o commit ser tratado como
final:

```
execute-sprint → verify-sprint (GATE: conforme?) → mini review (bem-feito?) → próximo
                     └─ NÃO CONFORME → PARA, reporta, não avança
```

**CONFORME** libera o fechamento e a orquestração segue; **NÃO CONFORME / PARCIAL** para o loop —
reporta para o `execute-sprint` (novo ciclo) ou decisão do usuário; o gate não corrige nem replaneja
sozinho.
