---
name: execute-sprint
description: >-
  Executa um único sprint de forma disciplinada: planeja antes de agir, implementa apenas o
  escopo do sprint, valida o entregável com prova objetiva reproduzível e faz commit — parando e
  reportando se a validação falhar. Achados fora do escopo são registrados em TECH_DEBT.md em vez
  de corrigidos em silêncio ou descartados. Use ao executar, rodar ou implementar um sprint, uma
  fase ou etapa de um plano/roadmap, ou um item com escopo e critério de aceite definidos —
  inclusive sprints de correção vindos de code review. Qualquer domínio (código, infra,
  documentação, dados).
argument-hint: "[sprint]"
allowed-tools: Bash(git status) Bash(git add *) Bash(git commit *) Bash(git diff *) Bash(git log *)
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.5.0"
---

# execute-sprint

Executa **um** sprint de um plano incremental, do começo ao fim, com disciplina de checkpoint:
transforma uma definição de sprint — escopo + restrições + entregável verificável — em trabalho
implementado, validado por prova objetiva e commitado. Se a validação falhar, **para e reporta**,
em vez de seguir por cima do erro.

Genérica: nenhuma linguagem, framework ou ferramenta embutida. Comandos concretos (validar,
commitar) vivem no `CLAUDE.md` do projeto — esta skill chama "o comando de validação do projeto",
nunca uma ferramenta específica.

## Pré-condições

Uma **definição de sprint** — tipicamente um arquivo `docs/sdd/sprints/NN-*.md` gravado pela
`decompose`; recebida como caminho, leia o arquivo — com, no mínimo: **escopo** (o que fazer),
**restrições** (o que NÃO fazer / não antecipar) e **entregável verificável** (o critério de
aceite). Se algum desses três estiver ausente ou ambíguo, resolva **antes** de tocar em código —
pergunte, ou aponte a lacuna. Não improvise um critério: executar sem entregável claro é executar
sem saber quando parar.

Controle de versão ativo — o commit ao final depende disso.

**Status do sprint:** quando a definição vem de um plano em `docs/sdd/sprints/`, mantenha a linha
`Status:` do arquivo via script — nunca à mão:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sdd_status.py" set <N> em-execucao` ao começar;
`set <N> executado` após o commit; `set <N> parou --nota "<etapa: motivo>"` ao parar. Sem plano em
arquivo, pule os `set` — o restante do procedimento é idêntico.

## Procedimento

**1. Ler o contexto do projeto primeiro.** Leia `CLAUDE.md` e a definição do sprint antes de
planejar. Não assuma convenções de memória — comando de teste, estilo de commit, ferramentas e
limites são propriedade do projeto e mudam entre projetos.

**2. Planejar antes de agir.** Produza um plano do que este sprint vai fazer — arquivos, abordagem,
como o entregável será provado. Em sessão interativa, apresente-o para aprovação antes de editar
(via plan mode, se disponível). Sob orquestração da `run-sprints`, a aprovação do plano de sprints
já cobre este passo — não pare para reaprovar cada sprint. Em ambos os casos, decisão de design com
mais de uma opção viável não se decide sozinho: apresente as opções com trade-offs e aguarde a
escolha — decisão de design é pergunta, não palpite. E se a própria definição do sprint tiver uma
inconsistência, sinalize para corrigir o documento na origem — não improvise um contorno que
mascara o defeito.

**3. Implementar apenas o escopo do sprint.** Nada além — não antecipe trabalho de sprints futuros,
nem para "adiantar" nem para fazer uma verificação passar. Se cumprir o escopo genuinamente exigir
tocar em algo fora dele, sinalize a tensão em vez de expandir em silêncio.

Se, ao trabalhar no escopo, você notar algo **fora dele** que merece atenção — código que foge do
padrão do módulo, um bug pré-existente sem relação com este sprint, uma refatoração que ficaria
melhor mas não é o que foi pedido —, **não corrija em silêncio e não descarte**: registre no
backlog com uma chamada (o script cria o `TECH_DEBT.md` se não existir):

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tech_debt.py" add \
  --item "<o problema, objetivo>" --onde "<arquivo/módulo>" \
  --motivo "fora do escopo do sprint <N>" --origem "sprint <N>" \
  --severidade <alta|media|baixa> --escopo <pontual|amplo>
```

Este é o destino padrão para tudo que é real mas não é deste sprint — o registro é o que impede um
achado válido de se perder por não ter para onde ir.

**Exceção — corrija na hora, sem registrar, quando todas as condições valerem:**
- o ajuste é **pontual** (um arquivo, uma função — não se espalha por várias classes/módulos);
- está **na mesma vizinhança** do que o sprint já está tocando (o mesmo arquivo, ou um vizinho
  direto que o sprint já editou);
- e **não muda contrato/interface** que outra parte do código dependa.

Fora dessas três condições — em especial se o ajuste tocaria muitos arquivos ou classes — é
**backlog, não correção incidental**: a decisão de abrir uma refatoração ampla é do usuário, não
uma consequência automática de ter passado por perto. O `--escopo` registrado ("pontual" ou
"amplo") é o que permite a uma sessão futura decidir se vira sprint via `decompose`.

**4. Validar o entregável com prova objetiva.** Rode as checagens do projeto (testes, lint, build)
— mas isso é o piso, não o aceite. O aceite é a **evidência específica que o entregável pede**:
exercite o caminho novo, mostre a saída esperada, demonstre o efeito. "Parece pronto" nunca é
aceite.

A prova precisa ser **reproduzível do zero** — sem depender de cache quente, arquivo de rodada
anterior, ou o mesmo processo que acabou de escrever o valor. Rode a partir de estado limpo; se o
comportamento é sensível a concorrência, ordem ou reinício, exercite sob essas condições. O gate
(`verify-sprint`) vai re-executar essa prova de forma independente — uma prova que só passa "aqui e
agora" será reprovada lá.

**5. Checkpoint — decidir avançar.** Compare o resultado com cada item do entregável.
- **Todos os itens passaram** → resumo curto do que foi feito e do resultado das checagens,
  **commit** com mensagem descritiva referenciando o sprint, e `sdd_status.py set <N> executado`.
  Se este sprint veio de um item do `TECH_DEBT.md` (via `decompose` com fonte backlog), feche o
  item: `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tech_debt.py" resolve <nº do item> --ref "sprint
  <N> / commit <hash>"` — o backlog só é confiável se fecha o que resolveu.
- **Qualquer item falhou** → **PARE.** Não commite, não avance, não tente "consertar por cima" sem
  entender. `sdd_status.py set <N> parou --nota "<o que falhou>"` e reporte com clareza: o que
  falhou, causa provável, o que precisa ser decidido ou corrigido. Aguarde. Não resolva itens do
  backlog — continuam abertos até de fato resolvidos.

**6. Não gerar resumo persistente paralelo.** Não crie arquivo de "memória" ou handoff sobre o que
*este* sprint fez — o estado é o commit + os arquivos + a linha `Status:`; a próxima execução relê
do repositório. Uma decisão de design nova vai em `CLAUDE.md`/ADR; achado fora do escopo vai no
backlog via script (passo 3); nenhum dos dois é resumo da execução.

## Formato de saída

- **Resumo de execução:** o que foi implementado, resultado das checagens, evidência do entregável
  — ou, em falha, o relatório do que impediu o avanço (o quê, causa, decisão pendente).
- **Commit** com mensagem descritiva referenciando o sprint — apenas quando o entregável passou.
- **Itens de débito técnico**, se algum foi registrado: liste as linhas de confirmação do
  `tech_debt.py`, para o usuário ver sem abrir o arquivo.
- **Nenhum artefato de memória** paralelo aos documentos do projeto — `TECH_DEBT.md` é backlog, não
  memória de execução.

## Fronteiras

Executa **um** sprint por invocação. Fora disso:
- Não decompõe um projeto em sprints — isso é `decompose`.
- Não audita código em busca de bugs — isso é `review-quality`.
- Não é o juiz independente de conformidade. A auto-verificação daqui ("rodei a prova e passou") é
  do executor; o julgamento independente é da `verify-sprint`, um subagent cego ao raciocínio do
  executor, que atua como gate depois desta skill.
- Não orquestra múltiplos sprints — isso é da skill de orquestração `run-sprints`, que roda esta
  uma vez por sprint (via subagent `sprint-executor`).
