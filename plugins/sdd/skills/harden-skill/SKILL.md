---
name: harden-skill
description: >-
  Constrói um eval EXECUTÁVEL para uma skill (do método de sprints ou outra) e mede o ganho REAL dela
  sobre um baseline sem a skill — para evoluí-la com base em evidência, não em intuição. A ideia
  central: uma fixture pequena e auto-contida onde o defeito só aparece na REEXECUÇÃO independente (não
  na leitura do código), um oráculo escondido que pontua, e dois braços (com a skill × sem) rodados e
  comparados. Use quando quiser endurecer, estressar, avaliar ou validar de verdade uma skill, medir se
  ela adiciona valor, ou descobrir onde ela falha. Dispare por "/harden-skill", "criar um eval
  executável para a skill X", "medir o lift da skill Y", "a skill Z vale mesmo?", "estressar/endurecer a
  skill", "essa skill melhora o resultado ou é só cerimônia?". NÃO cria a skill nem afina a descrição
  (isso é da skill-creator) — complementa-a com a medição executável que ela não faz. Aplica-se a
  qualquer skill cuja saída seja verificável.
---

# harden-skill

Esta skill **mede se uma skill vale** — e onde — construindo um **eval executável** e comparando a
skill (o braço **tratamento**) contra um **baseline** sem ela. O produto é um número honesto de *lift*
(quanto a skill melhora o resultado) e, a partir dele, melhorias concretas na skill ou fixtures de
regressão que travam o ganho.

Ela existe porque o eval **padrão** de uma skill (o que a `skill-creator` gera) roda sobre fixtures
**sintéticas e pequenas**, onde verificar é trivial — e por isso dá nota alta e **pouco informativa**:
não distingue "a skill funciona" de "qualquer modelo capaz já faria isto sem a skill". Esta skill
ataca justamente o que aquele eval não alcança: **o trabalho difícil**, onde descobrir o defeito e
provar que ele existe custa esforço.

## O princípio que faz o eval valer (leia antes de tudo)

O maior aprendizado, e o que torna um eval informativo: **raciocinar sobre um artefato não é
verificá-lo.** Um bom modelo, lendo um diff, quase sempre conclui que a prova "parece válida" — e erra
exatamente nos casos que importam. O valor de uma skill de verificação só aparece quando a fixture tem
esta propriedade:

> **O defeito passa VERDE na prova relatada e só é desmascarado por REEXECUÇÃO independente** — do
> estado limpo, exercitando a propriedade real.

Exemplos do arquétipo (todos auto-contidos e determinísticos):
- uma persistência que "prova" o round-trip por um **cache de processo**, mas o arquivo nunca é gravado
  em disco (só um processo novo revela);
- uma sincronização "provada" por um comando que **força a condição no instante do assert** (flaky);
- um teste de "cold start" que passa só por causa de um **artefato deixado** de uma rodada anterior;
- uma reserva sem trava que só **sobrevende sob concorrência**.

Se a fixture não tiver essa propriedade, o eval bate no **teto** (ler = descobrir → todo mundo acerta,
lift 0) ou no **piso** (nada é executável → todo mundo erra igual, lift 0). O lift real mora no meio:
**descobrir é difícil E verificar é possível mas custoso.**

## Procedimento

### 1. Nomear a propriedade discriminante

Diga, em uma frase, **o comportamento que a skill deveria garantir e que um executor sem ela deixaria
passar**. É a hipótese do eval. Sem isso, você mede ruído.

### 2. Construir a fixture executável (o passo que decide a validade)

Monte um alvo **pequeno, auto-contido e determinístico** com três peças:

- **A entrega** — o código com o defeito real, **de aparência inocente**. Nada de comentário
  `# BUG:` nem de nome de arquivo que entregue a resposta: se o código telegrafa o defeito, o baseline
  também acha de graça e o eval não mede nada. (É o erro mais fácil de cometer — e o mais fatal.)
- **A prova do executor** (`verify.py` ou equivalente) — **honesta e verde**: ela passa de verdade,
  mas por um caminho que **não exercita a propriedade real** (mesmo processo, cache quente, caminho
  feliz).
- **O oráculo escondido** (`oracle.py`) — a **reexecução independente** que desmascara: roda do estado
  limpo, exercita a propriedade real, e **falha**. Fica fora do que os braços veem.

### 3. Validar o instrumento ANTES de rodar

Rode o oráculo contra uma implementação **correta** (deve passar) e contra a **bugada** (deve falhar).
Se ele não discrimina, o eval é inútil — conserte o oráculo antes de gastar um único agente. Cuidado
com detecção **não-determinística** (ex.: corrida que só dispara com delay): force a condição
(barreira, `switchinterval` baixo, muitas rodadas) e confirme que o correto passa e o bugado falha de
forma estável. *(Ambos os erros — telegrafar o bug e um oráculo que não dispara — já aconteceram; por
isso este passo é obrigatório.)*

### 4. Rodar os dois braços — e, se der, em dois modelos

Em diretórios **isolados** (sem o oráculo/gabarito vazando), rode:
- **baseline** — um agente competente que só recebe a tarefa, sem a skill/stance;
- **tratamento** — o mesmo, **com** a skill (ou o stance que ela prescreve).

Rode em **≥ 2 modelos** (um forte e um fraco) sempre que puder: separa o que é mérito da **skill** do
que é mérito do **modelo**. Um controle de "entrega honesta" (que ambos devem ACEITAR) mede
**precisão** — um gate que reprova tudo é inútil.

### 5. Pontuar e ler honestamente

- **recall** = o braço pegou o defeito? · **precisão** = aceitou o trabalho honesto? · **lift** =
  tratamento − baseline.
- **Se o lift for ~0**, pergunte antes de comemorar ou enterrar: a fixture era fácil demais (teto)? a
  verificação não era executável (piso)? Um modelo forte **já faz** boa parte da disciplina sozinho —
  então meça o ganho onde ele importa: **descoberta difícil** e **fronteiras de decisão** (fechar/
  entregar), não em julgamentos triviais.

### 6. Alimentar de volta

Cada defeito que o **baseline erra e o tratamento pega** é o valor da skill — vire fixture de
regressão. Cada defeito que **ambos erram** é uma lacuna: ou a skill precisa evoluir (ex.: mandar
**re-executar** em vez de raciocinar), ou o valor não está ali. Escreva a melhoria na skill e re-rode.

## Formato de saída

```
# Harden — <skill> · propriedade: <a hipótese discriminante>
**Instrumento validado:** correto <n/n> · bugado <0/n>   (oráculo discrimina)

| fixture | baseline (haiku/opus) | tratamento (haiku/opus) | lift |
|---------|-----------------------|-------------------------|------|
| <nome>  | recall x/n · prec y/m | recall x/n · prec y/m   | +Δ   |

## Leitura
- Onde a skill ganhou / onde empatou com o baseline / onde o modelo já bastava.
## Melhorias propostas para a skill
- <derivadas dos defeitos que ambos erraram>
```

Um exemplo completo e rodável do arquétipo (entrega + prova verde + oráculo que desmascara) está em
[`assets/exemplo-prova-auto-validante/`](assets/exemplo-prova-auto-validante/) — copie e adapte.

## Princípios

- **Executável, não estático** — o defeito só vale se a reexecução o desmascara; leitura não basta.
- **Não telegrafar** — código de aparência inocente; comentário que entrega o bug invalida o eval.
- **Validar o instrumento primeiro** — oráculo tem de discriminar correto × bugado, de forma estável.
- **Separar skill de modelo** — dois braços, dois modelos; controle honesto para a precisão.
- **Lift honesto** — ~0 pode ser teto (fácil demais) ou piso (não-executável), não "a skill é ótima/
  inútil". O valor mora onde descobrir é difícil e verificar é possível-mas-custoso.

## Fronteiras (o que esta skill NÃO faz)

- **Não cria a skill nem afina a descrição/gatilho** — isso é da `skill-creator`. Esta skill
  **complementa**: a medição executável que a skill-creator não faz.
- **Não corrige a skill sozinha** — mede, aponta onde ela falha e propõe a melhoria; aplicar é uma
  edição (ou um sprint via `execute-sprint`).
- **Não substitui o eval de gatilho** — o eval padrão (a descrição dispara no prompt certo) continua
  valendo; esta skill cobre o eixo que ele não cobre: **o resultado vale?**
