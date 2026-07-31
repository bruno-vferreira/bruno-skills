---
name: review-quality
description: >-
  Audita código, configuração ou documentação em busca do que linters e validadores não pegam:
  divergências entre o contrato (schema, README, spec) e o comportamento real, bugs de lógica,
  suposições não verificadas, inconsistências entre camadas. Produz um relatório de achados
  priorizados por severidade — com cenário de falha concreto e correção sugerida — e registra
  também o que está correto. O escopo é parâmetro: o diff de um sprint (mini review) ou o
  repositório inteiro. Use sempre que o usuário pedir uma revisão, um code review, uma auditoria,
  uma checagem de qualidade, ou perguntar "isto está correto? está bem-feito?" — e ao final de um
  sprint, sobre o que acabou de ser implementado. Não corrige os achados nem verifica conformidade
  ao sprint (isso é da `verify-sprint`) — julga qualidade, em qualquer domínio.
argument-hint: "[escopo]"
context: fork
background: false
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.4.0"
---

# review-quality

Audita um corpo de trabalho — código, configuração ou documentação — em busca do que ferramentas
automáticas não detectam: divergências entre o que o contrato promete e o código faz, bugs de
lógica, suposições não verificadas, inconsistências entre camadas. Produz um relatório de achados
priorizados por severidade, cada um com localização, cenário de falha concreto e correção sugerida
— e reconhece também o que está correto, para que uma correção futura não quebre o que já funciona.

É a etapa de **qualidade**: encontra e descreve; não corrige (vira sprints via `decompose`,
executado por `execute-sprint`). Genérica: raciocina sobre contrato e lógica, não sobre sintaxe de
stack.

**O escopo é parâmetro.** Mesma skill roda sobre o diff de um sprint (mini review) ou o repositório
inteiro. Procedimento igual; muda a abrangência.

## Por que roda em subagent

Uma revisão lê muitos arquivos e gera muito conteúdo intermediário descartável — só o relatório
final interessa. Por isso esta skill roda em **subagent isolado** (`context: fork` no frontmatter):
a conversa principal recebe apenas o relatório. Consequência: o subagent não vê o histórico da
conversa — o escopo e o contexto necessários chegam na invocação.

## Pré-condições

- **O escopo do review** — arquivos, diff específico, ou repositório inteiro, recebido na
  invocação. Se vier ambíguo, não adivinhe em silêncio: declare no topo do relatório o escopo
  assumido e por quê — revisar tudo quando pediram só um diff gera ruído; só o diff quando queriam
  tudo deixa passar problema.
- **Documentos de contrato** do projeto — schema, README, spec, `CLAUDE.md`, exemplos commitados.
  Sem eles só dá para julgar o código contra si mesmo, não contra o que deveria fazer.

Checagens automáticas (fmt/lint/testes) são o piso, não o alvo — o ponto de partida é o que elas
não pegam.

## Procedimento

**1. Delimitar o escopo.** Confirme diff × repo inteiro e reúna os documentos de contrato. Registre
no relatório quais checagens automáticas já rodaram e seu status; se nenhum resultado estiver
disponível (ex.: review de repositório inteiro, sem execução anterior), rode as checagens do
projeto antes de prosseguir — elas são o piso que delimita o que este review procura.

**2. Ler o alvo e o contrato lado a lado.** Compare o comportamento real com o que o contrato
público promete. Divergência entre prometido e entregue é dos achados mais graves — especialmente
quando um artefato commitado no repositório expõe a divergência (ex.: um `exemplo.csv` que o código
nunca conseguiria gerar do jeito que está).

**3. Procurar as classes de problema que ferramentas não pegam:**
- **Bugs de lógica e dependência** — ordem implícita sem nada que a garanta.
- **Falhas silenciosas** — valor descartado sem erro (parâmetro aceito na interface, ignorado na
  implementação).
- **Suposições não verificadas** — constantes chutadas dependentes de fato externo não confirmado.
- **Colisões / efeitos globais** — estado compartilhado que uma execução concorrente corromperia.
- **Inconsistências entre camadas** — schema × conversor × implementação × docs contando histórias
  diferentes.

**Onde der para executar, execute.** Vários defeitos só são confirmáveis rodando: uma corrida você
exercita disparando acesso concorrente; um parâmetro ignorado você prova rodando e olhando a saída
real; um teste que só passa por estado prévio você desmascara rodando do zero. Um achado
**reproduzido** é confirmado, não suspeita — prefira sempre "disparei 50 reservas concorrentes de
estoque 10 e 50 passaram" a "acho que há uma corrida aqui".

**4. Classificar cada achado por severidade** (alta/média/baixa) com base no impacto real ao
usuário e probabilidade no uso normal — não na facilidade de conserto.

**5. Registrar cada achado com prova:** localização, descrição, **cenário de falha concreto**
(entrada/estado específico que produz o erro), correção sugerida. Achado sem cenário de falha é
suspeita, não achado. Quando houver mais de um caminho legítimo de correção, apresente alternativas
com trade-offs em vez de decidir sozinho.

**6. Registrar o que está correto** — notas positivas: decisões acertadas que não devem mudar. Não
é elogio, é proteção contra "consertar" algo que já funciona de propósito. Também obriga a não
inventar problema onde não há: se o código está correto, o relatório correto é curto.

**7. Achado fora do escopo delimitado vai para `TECH_DEBT.md`, não para o relatório principal.**
Num mini review (escopo = diff de um sprint), é comum notar algo relevante em código **adjacente**
ao diff, mas fora dele — não é o que este review foi pedido para julgar, e listá-lo junto ao
relatório do sprint mistura dois assuntos. Registre em `TECH_DEBT.md` na raiz do projeto (a partir
de [`assets/tech-debt-template.md`](assets/tech-debt-template.md) se não existir) com origem
"achado incidental de review", em vez de expandir o relatório para algo que não foi pedido ou
descartar a observação.

**8. Emitir o relatório.** Em subagent, retorne como resumo estruturado ao contexto principal.

## Formato de saída

Use exatamente este formato:

```
# Code Review — <alvo>
**Escopo:** <o que foi revisado — o diff do sprint X ou o repo inteiro>
**Toolchain:** <checagens automáticas rodadas e seu status>
       — nota: os achados abaixo são de lógica/contrato, que essas ferramentas não pegam.

## Resumo
| # | Severidade | Arquivo | Problema (uma linha) |
|---|------------|---------|-----------------------|
| 1 | Alta       | ...     | ...                   |

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

Se não houver achados, diga isso claramente e entregue só notas positivas e recomendação — "está
bem-feito" é resultado válido, não fracasso.

## Fronteiras

- Não corrige os achados — apenas encontra e descreve. Correção vira sprints via `decompose`,
  executada por `execute-sprint`.
- Não verifica conformidade ao sprint — julgar se o entregue corresponde ao *definido*
  (escopo/restrições/entregável) é da `verify-sprint`. Esta skill julga qualidade, não aderência ao
  combinado. Um código pode passar aqui e ainda ter desviado do sprint — e vice-versa.
- Não decompõe o próprio relatório em sprints — isso é `decompose`.
- Não executa sprints — é auditoria, não implementação.
