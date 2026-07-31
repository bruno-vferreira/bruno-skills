<!-- O plano é um diretório, não um documento único:
       docs/sdd/sprints/00-plano.md      ← o índice (primeira metade deste template)
       docs/sdd/sprints/NN-<slug>.md     ← um arquivo por sprint (segunda metade)
     A linha `Status:` de cada sprint é mantida por sdd_status.py — não a omita. -->

# Plano de Sprints — <projeto / alvo>            <!-- arquivo: 00-plano.md -->
**Fonte:** <docs/sdd/spec-X.md | relatório de review Y | TECH_DEBT.md itens N, M>

## Índice e sequência
| # | Sprint (arquivo) | Entregável (resumo) | Depende de | Por que nesta posição |
|---|------------------|---------------------|------------|-----------------------|
| 1 | 01-<slug>.md     |                     | —          |                       |
| 2 | 02-<slug>.md     |                     | 1          |                       |

<Sequência — um parágrafo com a lógica geral da ordem: contrato antes de consumo, dependências
técnicas, e por que os itens independentes ficaram nesta ordem (risco/severidade, vitória rápida).>

## Fora de escopo / fases futuras
- <o que ficou de fora do ciclo atual, com uma linha de por quê / quando entra>
- <itens que a fonte marcou como "para depois" e itens vagos demais que precisam voltar à spec>

---

# Sprint 01 — <título>                           <!-- arquivo: 01-<slug>.md -->
Status: pendente

**Contexto:** <o trecho da spec que este sprint realiza, ou o achado do review que ele corrige>
**Objetivo:** <a mudança de estado que este sprint entrega, em uma frase>

## Escopo
-

## Restrições
- <o que NÃO fazer / o que pertence a sprints futuros>

## Entregável (prova verificável)
- <a prova de aceite: como rodá-la a partir de estado limpo e qual propriedade real ela exercita>
- <quando a fonte é review: a prova de que aquele bug específico sumiu>

## Commit
- <mensagem de commit sugerida referenciando o sprint — quando o projeto usa controle de versão>
