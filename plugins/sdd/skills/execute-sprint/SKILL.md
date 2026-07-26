---
name: execute-sprint
description: >-
  Executa um único sprint de desenvolvimento de forma disciplinada: planeja antes de agir,
  implementa apenas o escopo do sprint, valida o entregável com prova objetiva e faz commit —
  parando e reportando se a validação falhar. Achados fora do escopo (bugs pré-existentes, código
  fora do padrão) são registrados em TECH_DEBT.md em vez de corrigidos em silêncio ou descartados —
  correção incidental só quando pontual e na mesma vizinhança do sprint. Use sempre que o usuário
  for executar, rodar ou implementar um sprint, uma fase, uma etapa de um plano/roadmap, ou um item
  de uma lista de tarefas com escopo e critério de aceite definidos — mesmo que ele não diga a
  palavra "sprint". Aplica-se a qualquer domínio (código, infraestrutura, documentação, dados).
  Aplica-se também a sprints de correção originados de code review.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.2.0"
---

# execute-sprint

Executa **um** sprint de um plano incremental, do começo ao fim, com disciplina de checkpoint:
transforma um prompt de sprint — escopo + restrições + entregável verificável — em trabalho
implementado, validado por prova objetiva e commitado. Se a validação falhar, **para e reporta**,
em vez de seguir por cima do erro.

Genérica: nenhuma linguagem, framework ou ferramenta embutida. Comandos concretos (validar,
commitar) vivem no `CLAUDE.md` do projeto — esta skill chama "o comando de validação do projeto",
nunca uma ferramenta específica.

## Pré-condições

Uma **definição de sprint** com, no mínimo: **escopo** (o que fazer), **restrições** (o que NÃO
fazer / não antecipar) e **entregável verificável** (o critério de aceite). Se algum desses três
estiver ausente ou ambíguo, resolva **antes** de tocar em código — pergunte, ou aponte a lacuna.
Não improvise um critério: executar sem entregável claro é executar sem saber quando parar.

Controle de versão ativo — o commit ao final depende disso.

## Procedimento

**1. Ler o contexto do projeto primeiro.** Leia `CLAUDE.md` e o prompt do sprint antes de
planejar. Não assuma convenções de memória — comando de teste, estilo de commit, ferramentas e
limites são propriedade do projeto e mudam entre projetos.

**2. Planejar antes de agir.** Produza um plano do que este sprint vai fazer — arquivos, abordagem,
como o entregável será provado. Quando o ambiente suportar, apresente para aprovação antes de
editar. Se houver decisão de design com mais de uma opção viável, não decida sozinho: apresente as
opções com trade-offs e aguarde a escolha — decisão de design é pergunta, não palpite.

**3. Implementar apenas o escopo do sprint.** Nada além — não antecipe trabalho de sprints futuros,
nem para "adiantar" nem para fazer uma verificação passar. Se cumprir o escopo genuinamente exigir
tocar em algo fora dele, sinalize a tensão em vez de expandir em silêncio.

Se, ao trabalhar no escopo, você notar algo **fora dele** que merece atenção — código que foge do
padrão do módulo, um bug pré-existente sem relação com este sprint, uma refatoração que ficaria
melhor mas não é o que foi pedido —, **não corrija em silêncio e não descarte**: registre em
`TECH_DEBT.md` na raiz do projeto (crie a partir de
[`assets/tech-debt-template.md`](assets/tech-debt-template.md) se ainda não existir). Isto é o
destino padrão para tudo que é real mas não é deste sprint — o registro é o que impede um achado
válido de se perder por não ter para onde ir.

**Exceção — corrija na hora, sem registrar, quando todas as condições valerem:**
- o ajuste é **pontual** (um arquivo, uma função — não se espalha por várias classes/módulos);
- está **na mesma vizinhança** do que o sprint já está tocando (o mesmo arquivo, ou um vizinho
  direto que o sprint já editou);
- e **não muda contrato/interface** que outra parte do código dependa.

Fora dessas três condições — em especial se o ajuste tocaria muitos arquivos ou classes — é
**backlog, não correção incidental**: a decisão de abrir uma refatoração ampla é do usuário, não
uma consequência automática de ter passado por perto. Registre o item com escopo estimado
("pontual" ou "amplo") para uma sessão futura (sua ou de outra pessoa) decidir se vira sprint via
`decompose`.

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
- **Todos os itens passaram** → resumo curto do que foi feito e do resultado das checagens, e
  **commit** com mensagem descritiva referenciando o sprint. Se este sprint veio de um item do
  `TECH_DEBT.md` (via `decompose` com fonte backlog), risque o item na tabela "Itens abertos" e
  mova para "Itens resolvidos" com a referência do commit — o backlog só é confiável se fecha o
  que resolveu, senão acumula itens já corrigidos e ninguém confia mais nele.
- **Qualquer item falhou** → **PARE.** Não commite, não avance, não tente "consertar por cima" sem
  entender. Reporte com clareza: o que falhou, causa provável, o que precisa ser decidido ou
  corrigido. Aguarde. Não mexa no `TECH_DEBT.md` — o item continua aberto até de fato resolvido.

**6. Não gerar resumo persistente paralelo.** Não crie arquivo de "memória" ou handoff sobre o que
*este* sprint fez — o estado é o commit + os arquivos, a próxima execução relê do repositório. Isso
não conflita com o passo 3: `TECH_DEBT.md` não resume o sprint, registra achados que **não são**
deste sprint — é backlog de trabalho futuro, não handoff do trabalho atual. Uma decisão de design
nova sobre o que foi implementado vai em `CLAUDE.md`/ADR; um achado fora do escopo vai em
`TECH_DEBT.md`; nenhum dos dois é um resumo solto da execução.

## Formato de saída

- **Resumo de execução:** o que foi implementado, resultado das checagens, evidência do entregável
  — ou, em falha, o relatório do que impediu o avanço (o quê, causa, decisão pendente).
- **Commit** com mensagem descritiva referenciando o sprint — apenas quando o entregável passou.
- **Itens de débito técnico**, se algum foi encontrado e registrado: liste o que foi adicionado a
  `TECH_DEBT.md` nesta execução, para o usuário ver sem precisar abrir o arquivo.
- **Nenhum artefato de memória** paralelo aos documentos do projeto — `TECH_DEBT.md` é backlog, não
  memória de execução.

## Princípios (quando o roteiro não cobrir o caso)

- **Escopo fechado** — implemente o sprint, nada além.
- **Achado não é descarte nem correção automática** — fora do escopo e pontual pode ser corrigido
  na hora (regras no passo 3); fora do escopo e amplo é sempre `TECH_DEBT.md`, nunca "já que
  encontrei, aproveito e arrumo".
- **Prova, não sensação** — o entregável define a evidência; "parece pronto" não é aceite.
- **Parar no vermelho** — falha de validação interrompe e reporta; não se segue por cima.
- **Planejar antes de agir** — decisão de design vira pergunta, não suposição.
- **Corrigir na origem** — se o próprio prompt/plano tiver uma inconsistência, sinalize para
  corrigir o documento, não improvise um contorno que mascara o defeito.
- **Genérica** — nenhuma ferramenta ou linguagem embutida; o projeto pluga isso via `CLAUDE.md`.

## Fronteiras

Executa **um** sprint por invocação. Fora disso:
- Não decompõe um projeto em sprints — isso é `decompose`.
- Não audita código em busca de bugs — isso é `review`.
- Não é o juiz independente de conformidade. A auto-verificação daqui ("rodei a prova e passou") é
  do executor; o julgamento independente é da `verify-sprint`, um subagent cego ao raciocínio do
  executor, que atua como gate depois desta skill.
- Não orquestra múltiplos sprints — isso é das skills de orquestração (`build-project` /
  `review-and-fix`), que chamam esta uma vez por sprint.

## Variantes por tecnologia

Genérica por decisão. Se surgirem variantes por stack, cada uma entra como
`references/<tecnologia>.md` descrevendo os comandos de validação e commit daquela tecnologia —
lida sob demanda, núcleo permanece idêntico.
