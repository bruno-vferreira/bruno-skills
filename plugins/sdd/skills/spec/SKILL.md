---
name: spec
description: >-
  Dispare com "/spec" e sempre que o usuário quiser definir O QUE construir antes de partir para o
  código. Use quando ele: começa a descrever um projeto, funcionalidade ou sistema novo; pede para
  levantar ou organizar requisitos ainda soltos; quer montar o escopo ou fechar o contrato do que
  será construído; quer entender bem o problema antes de implementar; recebeu requisitos vagos e
  quer transformá-los numa spec, apontando ambiguidades; ou avisa que vai mandar os requisitos aos
  poucos. Vale mesmo sem a palavra "especificação" — reconheça a intenção por trás de frases como
  "me ajuda a levantar os requisitos", "quero entender antes de codar", "monta o escopo disso". A
  skill é conversacional: confirma o entendimento passo a passo, registra decisões com o racional,
  caça lacunas e consolida um documento de especificação estável. NÃO escreve código, não planeja
  execução e não decompõe em sprints — isso é da `decompose`.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.2.0"
---

# spec

Transforma requisitos brutos e conversacionais em uma **especificação rigorosa**: captura o que o
usuário quer, confirma a cada passo, registra **decisões com racional**, caça o que está faltando
ou ambíguo — resolvendo antes de seguir. O produto alimenta a `decompose`.

É a fase de **entender antes de fazer**: sem código, sem plano de execução, sem sprint — só
capturar, confirmar e consolidar o contrato do que será construído. Genérica: raciocina sobre
intenção, decisão e completude, não sobre stack.

## Modo conversacional

A entrada chega em conversa, muitas vezes em pedaços — o valor está no vaivém. **Erro central a
evitar:** receber "quero construir X" e despejar de imediato uma spec completa, com decisões
inventadas para preencher o que o usuário não disse. Isso troca entendimento por ilusão de
completude, e a decomposição herda suposições que ninguém validou.

Ritmo padrão: anote o que entendeu, confirme, pergunte o que falta, só feche quando o usuário
sinalizar.

## Pré-condições

- Requisitos do usuário — podem chegar incrementalmente, em várias mensagens. Se ele disser "vou
  mandar aos poucos", a spec fica **aberta** até o sinal de fechamento.
- Nenhuma dependência de ferramenta — genérica, só raciocina e registra.

## Princípios

1. **Entender antes de fazer.** Nenhum código ou plano de execução aqui. Se o usuário descreve uma
   solução técnica, capture como decisão — não a implemente.
2. **Confirmar, não presumir.** Reflita de volta cada bloco de requisito ("anotado: X, Y, Z") para
   o usuário corrigir na hora. Suposição não confirmada é dívida que vence na decomposição.
3. **Decisão registrada é decisão rastreável.** Toda escolha relevante vira decisão anotada com o
   porquê. Havendo alternativas, mostre os trade-offs e deixe o usuário escolher; se ele delegar,
   assuma um default sensato e registre-o explicitamente como tal. Nenhuma escolha invisível.
4. **Incremental por padrão.** Não declare "pronto" por conta própria enquanto o usuário estiver
   alimentando requisitos — fechar cedo é o mesmo erro de despejar a spec completa, só distribuído
   no tempo.
5. **Lacuna é risco.** Cace ativamente casos de borda, formatos de entrada/saída, restrições,
   estado, ambientes, o que não foi dito. Cada lacuna vira **pergunta** ou **default registrado
   como decisão** — nunca um buraco silencioso.
6. **Genérica.** Sem ferramentas ou stacks embutidas.

## Procedimento

**1. Capturar incrementalmente.** A cada bloco de requisito, registre de forma sucinta e explícita
— "anotado: X, Y, Z". Não trate a spec como completa até o usuário sinalizar.

**2. Confirmar passo a passo.** Reflita de volta e deixe o usuário corrigir antes de prosseguir.
Prefira confirmar em pedaços curtos ("o filtro é por período, inclusivo nas duas pontas — certo?")
a acumular suposições e validar só no fim.

**3. Registrar decisões com racional.** Toda escolha relevante vira decisão anotada com o porquê.
Havendo alternativas reais, apresente trade-offs; se o usuário delegar, assuma um default sensato e
registre como decisão explícita ("default assumido: ... porque ..."). Uma decisão não escrita é uma
decisão que a `decompose` vai tomar de novo, provavelmente diferente.

**4. Caçar lacunas.** Procure o que não foi dito: casos de borda, formatos de entrada/saída,
restrições, onde mora o estado, ambientes, volumes, comportamento no erro.

Vá além do que o usuário listou e cheque as **obrigações universais do domínio** — as que quase
nenhum requisito bruto menciona, mas que todo sistema daquele tipo precisa cumprir:
- **Segurança** — segredos e senhas nunca em texto claro.
- **Concorrência** — acesso simultâneo seguro, sem corrida, sem oversell.
- **Integridade de estado** — operações atômicas e idempotentes; nada corrompido por reexecução ou
  sequência inesperada.
- **Conservação** — em dinheiro/estoque, nada some nem duplica; sem saldo negativo.

Cada uma que se aplicar vira pergunta ou default registrado — nunca fica implícita. Um invariante
que a spec não nomeia é um invariante que a `decompose` não tem como transformar em entregável.

Quando puder resolver ou propor, faça-o antes de perguntar. Para o resto, no máximo uma pergunta
focada por vez; para o que ficar em aberto, proponha um default e marque como decisão.

**5. Confirmar completude ativamente.** Antes de consolidar, cheque o que pode faltar e pergunte —
não declare "pronto" pela sensação: "cobrimos parsing, filtro e saída; falta dizer o que fazer com
linha malformada e onde grava a saída — define agora ou deixo default?" Se o usuário ainda vai
mandar coisas, a completude não é sua para declarar.

**6. Consolidar.** Quando o usuário sinalizar fechamento, produza o documento estruturado abaixo.
Ele precisa ser autossuficiente — quem for decompor lê a spec, não reabre a conversa.

## Formato de saída

Use o esqueleto em [`assets/spec-template.md`](assets/spec-template.md). Estrutura mínima:
visão geral, requisitos (funcionais/não-funcionais), decisões com racional e origem, contrato/
interface (quando houver), restrições e não-objetivos, pontos em aberto.

Notas de preenchimento:
- **Decisões** é o coração do documento — todo default assumido aparece aqui, marcado como tal na
  coluna Origem.
- **Contrato/interface** só entra quando fizer sentido (API, formato de arquivo, schema). Não force
  a seção em projeto sem interface pública.
- **Pontos em aberto** é resultado válido: uma spec pode fechar com itens por decidir, desde que
  nomeados — lacuna declarada é melhor que buraco silencioso.

## Fronteiras

- Não decompõe em sprints (`decompose` consome esta saída).
- Não implementa nada — se o usuário empurrar para "já começa a codar", registre a intenção técnica
  como decisão, mas não a execute.
- Não faz plano de execução — entrega o contrato do *quê*, não o roteiro do *como*.
- É a etapa de entendimento, anterior a tudo. Único produto: a especificação.

## Variantes por tecnologia

Agnóstica por decisão: capturar intenção, decisão e completude não muda entre domínios. Se surgir
necessidade de guia específico (o que costuma virar lacuna em tal área), entra como
`references/<tema>.md`, lido sob demanda.
