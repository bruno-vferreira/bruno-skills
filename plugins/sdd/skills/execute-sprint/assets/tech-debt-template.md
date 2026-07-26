# Débito Técnico

Backlog de itens fora do escopo do trabalho em andamento no momento em que foram encontrados —
refatorações, bugs pré-existentes, inconsistências — que não foram corrigidos ali por
disciplina de escopo fechado. Cada item aqui é uma **entrada candidata a virar sprint** via
`decompose` (fonte = "backlog de débito técnico").

Este arquivo é a fonte de verdade entre sessões: nenhuma skill mantém memória própria do que
encontrou. Se não está aqui, não sobreviveu à sessão que o encontrou.

## Convenção de entrada

Cada item é uma linha nesta tabela — sucinto o bastante para caber em uma linha, com contexto
suficiente para uma sessão futura sem memória desta decidir se vale virar sprint.

| # | Item | Onde | Por que não foi corrigido agora | Origem | Severidade | Escopo estimado |
|---|------|------|----------------------------------|--------|-------------|------------------|
| 1 | <descrição objetiva> | <arquivo/módulo/classe> | <fora do escopo do sprint N / achado incidental de review / ...> | <sprint N \| review de \<data\> \| observação avulsa> | alta/média/baixa | pontual (1 arquivo) / amplo (N arquivos, cortar em sprint próprio) |

- **Item** — o problema em si, objetivo: "classe `X` não segue o padrão de injeção de dependência
  usado no resto do módulo", não "código meio bagunçado ali".
- **Escopo estimado** é o que decide o destino: **pontual** é candidato a correção imediata na
  próxima vez que alguém mexer naquele arquivo por qualquer motivo; **amplo** (mexe em muitos
  arquivos/classes) é candidato a **sprint dedicado** de refatoração, nunca corrigido de
  passagem dentro de outro sprint.
- Itens **resolvidos** não são apagados — marque `~~riscado~~` com a referência do sprint/commit
  que resolveu, para o backlog também servir de histórico do que já foi endurecido.

## Itens abertos

| # | Item | Onde | Por que não foi corrigido agora | Origem | Severidade | Escopo estimado |
|---|------|------|----------------------------------|--------|-------------|------------------|

## Itens resolvidos

| # | Item | Resolvido em |
|---|------|--------------|
