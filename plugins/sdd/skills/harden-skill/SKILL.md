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
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.2.0"
---

# harden-skill

Mede se uma skill vale — e onde — construindo um **eval executável** e comparando a skill (braço
**tratamento**) contra um **baseline** sem ela. Produto: um número honesto de *lift* (quanto a skill
melhora o resultado) e, a partir dele, melhorias concretas ou fixtures de regressão que travam o
ganho.

Existe porque o eval padrão de uma skill (o que a `skill-creator` gera) roda sobre fixtures
sintéticas e pequenas, onde verificar é trivial — dá nota alta e pouco informativa, sem distinguir
"a skill funciona" de "qualquer modelo capaz já faria isto sem ela". Esta skill ataca o que aquele
eval não alcança: o trabalho difícil, onde descobrir o defeito e provar que ele existe custa
esforço.

## O princípio que faz o eval valer

**Raciocinar sobre um artefato não é verificá-lo.** Um bom modelo, lendo um diff, quase sempre
conclui que a prova "parece válida" — e erra exatamente nos casos que importam. O valor de uma
skill de verificação só aparece quando a fixture tem esta propriedade:

> O defeito passa VERDE na prova relatada e só é desmascarado por REEXECUÇÃO independente — do
> estado limpo, exercitando a propriedade real.

Arquétipos (todos auto-contidos e determinísticos): uma persistência que "prova" round-trip por
cache de processo, mas o arquivo nunca é gravado (só processo novo revela); uma sincronização
"provada" forçando a condição no instante do assert (flaky); um teste de cold start que passa por
um artefato deixado de rodada anterior; uma reserva sem trava que só sobrevende sob concorrência.

Sem essa propriedade, o eval bate no teto (ler = descobrir, todo mundo acerta, lift 0) ou no piso
(nada é executável, todo mundo erra igual, lift 0). O lift real mora no meio: descobrir é difícil E
verificar é possível mas custoso.

## Procedimento

**1. Nomear a propriedade discriminante.** Em uma frase: o comportamento que a skill deveria
garantir e que um executor sem ela deixaria passar. É a hipótese do eval — sem isso, você mede
ruído.

**2. Construir a fixture executável** (o passo que decide a validade) com três peças:
- **A entrega** — código com o defeito real, de aparência inocente. Nada de comentário `# BUG:` ou
  nome de arquivo que entregue a resposta: se o código telegrafa o defeito, o baseline acha de
  graça e o eval não mede nada. Erro mais fácil de cometer, e o mais fatal.
- **A prova do executor** (`verify.py`) — honesta e verde: passa de verdade, mas por caminho que
  não exercita a propriedade real (mesmo processo, cache quente, caminho feliz).
- **O oráculo escondido** (`oracle.py`) — a reexecução independente que desmascara: roda do estado
  limpo, exercita a propriedade real, e falha. Fora do que os braços veem.

**3. Validar o instrumento antes de rodar.** Rode o oráculo contra implementação correta (deve
passar) e bugada (deve falhar). Se não discrimina, o eval é inútil — conserte antes de gastar um
agente. Cuidado com detecção não-determinística (corrida que só dispara com delay): force a
condição e confirme estabilidade.

**4. Rodar os dois braços — e, se der, em dois modelos.** Em diretórios isolados: **baseline**
(agente competente sem a skill), **tratamento** (mesmo, com a skill). Rode em ≥2 modelos quando
possível (um forte, um fraco) — separa mérito da skill de mérito do modelo. Um controle de "entrega
honesta" (que ambos devem ACEITAR) mede precisão; um gate que reprova tudo é inútil.

**5. Pontuar e ler honestamente.** recall = pegou o defeito? precisão = aceitou o trabalho honesto?
lift = tratamento − baseline. Se o lift for ~0, pergunte antes de concluir: fixture fácil demais
(teto)? verificação não executável (piso)? Meça o ganho onde importa — descoberta difícil e
fronteiras de decisão — não em julgamentos triviais que um modelo forte já faz sozinho.

**6. Alimentar de volta.** Defeito que o baseline erra e o tratamento pega = valor da skill, vira
fixture de regressão. Defeito que ambos erram = lacuna: skill precisa evoluir (ex.: mandar
re-executar em vez de raciocinar) ou o valor não está ali. Escreva a melhoria e re-rode.

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

Exemplo completo e rodável do arquétipo (entrega + prova verde + oráculo) em
[`assets/exemplo-prova-auto-validante/`](assets/exemplo-prova-auto-validante/) — copie e adapte.
Exemplo de relatório final (com × sem a skill, com veredito) em
[`assets/exemplo-resultado.md`](assets/exemplo-resultado.md).

## Princípios

- **Executável, não estático** — o defeito só vale se a reexecução o desmascara; leitura não basta.
- **Não telegrafar** — código de aparência inocente; comentário que entrega o bug invalida o eval.
- **Validar o instrumento primeiro** — oráculo discrimina correto × bugado, de forma estável.
- **Separar skill de modelo** — dois braços, dois modelos; controle honesto para precisão.
- **Lift honesto** — ~0 pode ser teto ou piso, não "a skill é ótima/inútil". O valor mora onde
  descobrir é difícil e verificar é possível-mas-custoso.

## Fronteiras

- Não cria a skill nem afina descrição/gatilho — isso é `skill-creator`. Complementa: a medição
  executável que ela não faz.
- Não corrige a skill sozinha — mede, aponta a falha, propõe melhoria; aplicar é edição (ou sprint
  via `execute-sprint`).
- Não substitui o eval de gatilho — o padrão (a descrição dispara no prompt certo) continua
  valendo; esta skill cobre o eixo que ele não cobre: o resultado vale?
