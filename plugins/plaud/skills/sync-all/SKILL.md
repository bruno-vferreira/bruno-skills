---
name: sync-all
description: >-
  Carga TOTAL das gravações do Plaud para o disco local, via Plaud MCP,
  IGNORANDO o checkpoint. Dispare com "/plaud:sync-all" e quando o usuário
  quiser "baixar tudo do Plaud", "sincronizar tudo do zero", "rebaixar todas as
  gravações", "reprocessar/reconstruir minhas notas do Plaud", ou "ignorar o
  checkpoint e trazer tudo". Reprocessa TODAS as gravações (reescreve os
  markdowns; o áudio já baixado é pulado para evitar retráfego) e, ao final,
  REESCREVE o checkpoint em .plaud/checkpoint.json refletindo o estado completo.
  Para o dia a dia (baixar só o que falta, respeitando o checkpoint), use a skill
  sync. Não faz upload nem altera nada no servidor Plaud.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.1.0"
---

# Plaud sync-all (carga total)

Baixa **tudo**, **ignorando o checkpoint** para decidir o que processar: percorre **todas** as
gravações do servidor, regrava o `nota.md` de cada uma e, ao final, **reescreve** o
`.plaud/checkpoint.json` para refletir o estado completo (inclusive removendo registros órfãos cujo
`nota.md` não existe mais em disco).

É a **irmã** da skill `sync`. A diferença é só a **política**: a `sync` respeita o checkpoint e baixa
apenas o que falta; a `sync-all` ignora o checkpoint (não roda o `diff`) e reprocessa tudo, terminando
com um `finalize --rebuild`. Ambas usam o mesmo **motor** `scripts/plaud_sync.py` — esta skill
**orquestra** o MCP; o motor faz o trabalho determinístico e **nunca** chama o MCP.

## Quando usar

Quando o usuário quer uma **carga total** ou uma **reconstrução**: primeira sincronização, "baixa tudo
do zero", "reprocessa minhas notas", ou quando o checkpoint pode estar inconsistente e ele quer
regravar tudo. Para o uso incremental do dia a dia, é a skill **`sync`**.

É uma **operação em lote e custosa**: faz **uma** chamada `get_file` por gravação, então numa
biblioteca grande é lenta e consome quota do MCP. Se houver muitas gravações, vale confirmar com o
usuário antes de disparar — e, no dia a dia, preferir a `sync`.

## Pré-condições

- **Plaud MCP.** Este plugin **empacota** o servidor Plaud MCP em `.mcp.json`
  (`https://mcp.plaud.ai/mcp`, `type: http`): habilitar o plugin já o carrega, com OAuth no primeiro
  uso. Tools com prefixo **`mcp__plaud__*`** (`list_files`, `get_file`, `get_current_user`). Se o
  usuário usa o conector "claude.ai Plaud", o prefixo é `mcp__claude_ai_Plaud__*`. Em qualquer caso,
  use os tools equivalentes por capacidade.
- **`python3`** (>= 3.8).
- **Diretório de destino** = `cwd` (o `.plaud/` é criado ali), ou a pasta indicada pelo usuário.

## Localizar o motor

```
ENGINE="${CLAUDE_PLUGIN_ROOT}/scripts/plaud_sync.py"
# Se CLAUDE_PLUGIN_ROOT não estiver definido, o motor está em ../../scripts/plaud_sync.py
# relativo a ESTA SKILL.md (a partir de skills/sync-all/). Confirme com `test -f "$ENGINE"`.
ROOT="$(pwd)"          # diretório de destino
TMP="$(mktemp -d)"     # temporários privados desta execução — APAGUE no fim (contêm URLs assinadas)
```

## Procedimento

O princípio é o mesmo da `sync` — **você chama o MCP; o motor cuida do disco** — mas **sem o passo de
diff**: aqui processa-se **todas** as gravações. O JSON de cada tool do MCP deve ser **salvo em
arquivo temporário privado** e passado ao motor via **stdin**.

### 1. Listar TODAS as gravações do servidor (paginando)

Chame `list_files` com `page_size: 100`, começando em `page: 1`, e **incremente `page` até uma página
vir vazia** (sem itens). Salvaguarda: pare também se uma página trouxer **menos itens que a anterior**
(robusto caso o servidor limite o `page_size`). Junte todos os itens numa lista — esta é a lista
**completa** a reprocessar (não há `diff`).

### 2. Reprocessar cada gravação

Para **cada** `id` da lista (todas), um por vez:

1. Chame `get_file` com esse `id`. **Se falhar**, **pule e siga** (conte como falha; será reprocessada
   num próximo run). Não rode o `save` para um id cujo `get_file` falhou.
2. Se teve sucesso, salve o JSON num arquivo temporário **novo** em `"$TMP"`
   (`F="$(mktemp "$TMP/file.XXXXXX.json")"`).
3. Rode o motor e apague o temporário:
   ```
   python3 "$ENGINE" save --root "$ROOT" < "$F"
   rm -f "$F"
   ```
   O `save` regrava `recordings/<data>-<slug>/nota.md` e baixa `audio.mp3` **pulando se já existir**
   não-vazio (mantém o markdown atualizado sem rebaixar o binário à toa).

### 3. (Opcional) Identificar o usuário

Chame `get_current_user` e guarde `id`/`nickname` para carimbar o checkpoint.

### 4. Reescrever o checkpoint (finalize --rebuild)

```
python3 "$ENGINE" finalize --root "$ROOT" --rebuild --user-id "<id>" --user-nickname "<nickname>"
```

O `--rebuild` **reescreve** o checkpoint a partir do estado real em disco: remove registros cujo
`nota.md` não existe mais (órfãos de um checkpoint antigo/inconsistente) e recomputa os campos de topo
(`version`, `last_synced_at`, `last_created_at`). É isto que torna a `sync-all` uma **reconstrução**, e
não só um "baixar o que falta". Se você **pulou o passo 3**, rode sem as flags `--user-*` (o usuário
anterior no checkpoint é preservado).

### 5. Limpar e reportar

```
rm -rf "$TMP"
```

Resuma: total de gravações processadas, quantas com áudio baixado vs. pulado (já existente), quantas
falharam (`get_file` ou `audio: failed`), e que o checkpoint foi **reescrito** (quantos registros ao
final; quantos órfãos removidos, se algum).

## Garantias e limites

- **Ignora o checkpoint na decisão, reescreve no fim.** É a distinção central em relação à `sync`.
- **Segurança:** o motor nunca grava URLs assinadas (`presigned_url`, `data_link`) no `nota.md` nem no
  checkpoint — só o `id` do Plaud. Os payloads do MCP passam por temporários **privados** em `"$TMP"`
  (`mktemp -d`) e são apagados ao final.
- **Não rebaixa áudio à toa:** `save` pula o `audio.mp3` já presente não-vazio; a carga total regrava o
  markdown mas evita retráfego do binário.
- **Reescreve TODOS os `nota.md`:** a carga total regrava cada `nota.md` a partir do servidor —
  **edições manuais** feitas nesses arquivos serão **descartadas** (o `audio.mp3` é preservado; só o
  markdown é regravado). Se o usuário anota nas notas, prefira a `sync`, que só toca o que falta.
- **Idempotente:** rodar de novo converge para o mesmo estado.

## Fronteiras (o que esta skill NÃO faz)

- **Não é a incremental** — baixar só o que falta, respeitando o checkpoint, é a skill `sync`.
- **Não faz upload** nem edita/apaga nada no servidor Plaud (só leitura/download).
- **Não apaga** os áudios/markdowns locais de gravações que sumiram do servidor — o `--rebuild` só poda
  **registros** do checkpoint sem pasta em disco; não remove arquivos (sem exclusão destrutiva).
- **Não baixa a transcrição polida** (`transaction_polish`) nesta versão.
