---
name: sync
description: >-
  Sincroniza de forma INCREMENTAL as gravações do Plaud para o disco local, via
  Plaud MCP. Dispare com "/plaud:sync" e sempre que o usuário quiser "sincronizar
  o Plaud", "baixar as gravações novas", "atualizar minhas reuniões do Plaud",
  "puxar as transcrições/notas do Plaud", ou "trazer o que tem de novo no Plaud".
  Baixa só o que falta (respeita o checkpoint em .plaud/checkpoint.json): para
  cada gravação nova ou incompleta grava um markdown com frontmatter (resumo,
  tópicos e transcrição) e o áudio mp3, e atualiza o checkpoint. Para baixar TUDO
  ignorando o checkpoint, use a skill sync-all. Não faz upload nem altera nada no
  servidor Plaud.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.1.0"
---

# Plaud sync (incremental)

Sincroniza **servidor → local** de forma **incremental**: baixa apenas as gravações que ainda não
estão completas no disco, respeitando o `checkpoint` em `.plaud/`. Cada gravação vira uma pasta com
`nota.md` (frontmatter + resumo + tópicos + transcrição) e `audio.mp3`.

O trabalho determinístico (parsear o retorno do MCP, formatar o markdown, baixar o áudio, escrever o
checkpoint) é do **motor** `scripts/plaud_sync.py`. Esta skill **orquestra**: chama o MCP e alimenta
o motor. O motor **nunca** chama o MCP — quem chama é você (a skill).

## Quando usar

Quando o usuário quer trazer o que há de novo no Plaud sem rebaixar o que já tem: "sincroniza o
Plaud", "baixa as gravações novas", "atualiza minhas reuniões". Para **carga total** (ignorar o
checkpoint e reprocessar tudo), use a skill **`sync-all`**.

## Pré-condições

- **Plaud MCP conectado.** Os tools observados têm o prefixo `mcp__claude_ai_Plaud__*`
  (`list_files`, `get_file`, `get_current_user`). Se o servidor Plaud do usuário expuser outro
  prefixo, use os tools equivalentes por capacidade (listar gravações / obter uma gravação / usuário
  atual).
- **`python3`** (>= 3.8) disponível no shell.
- **Diretório de destino** = o diretório de trabalho atual (`cwd`). O `.plaud/` é criado ali. Se o
  usuário indicar outra pasta, use-a como `--root`.

## Localizar o motor

O motor fica em `<raiz-do-plugin>/scripts/plaud_sync.py`. Resolva o caminho assim:

```
ENGINE="${CLAUDE_PLUGIN_ROOT}/scripts/plaud_sync.py"
# Se CLAUDE_PLUGIN_ROOT não estiver definido, o motor está relativo a ESTA SKILL.md,
# em ../../scripts/plaud_sync.py (a partir de skills/sync/). Confirme com `test -f "$ENGINE"`.
ROOT="$(pwd)"   # diretório de destino do sincronismo
```

## Procedimento

Siga em ordem. O princípio é: **você chama o MCP; o motor cuida do disco.** O JSON que cada tool do
MCP retorna deve ser **salvo em um arquivo temporário** e passado ao motor via **stdin** (evita
problemas de escaping ao colar JSON grande no shell).

### 1. Listar as gravações do servidor (paginando)

Chame `list_files` com `page_size: 100`, começando em `page: 1`, e vá incrementando `page` até a
página vir com menos itens que `page_size` (ou vazia). Junte todos os itens num único JSON no formato
`{"data": [ ...todos os itens... ]}` e salve em, por exemplo, `/tmp/plaud_list.json`.

### 2. Descobrir o que falta (diff)

```
python3 "$ENGINE" diff --root "$ROOT" < /tmp/plaud_list.json
```

A saída é um JSON `{"to_sync": [...], "skipped": [...], "counts": {...}}`. Cada item de `to_sync` tem
`id`, `name` e `reason` (`novo` ou `incompleto`). Se `to_sync` estiver vazio, **não há nada novo** —
pule para o passo 5 (finalize) e reporte "nada novo".

### 3. Baixar cada gravação pendente

Para **cada** `id` em `to_sync`:

1. Chame `get_file` com esse `id` (o retorno traz metadados, a `presigned_url` do áudio, a
   transcrição, o outline e a nota-resumo).
2. Salve o JSON retornado em um arquivo temporário, ex. `/tmp/plaud_file.json`.
3. Rode o motor:
   ```
   python3 "$ENGINE" save --root "$ROOT" < /tmp/plaud_file.json
   ```
   O `save` cria `recordings/<data>-<slug>/nota.md`, baixa `audio.mp3` da `presigned_url` (pulando se
   já existir não-vazio) e atualiza o registro daquele `id` no checkpoint. Ele imprime um status JSON
   (`{"id", "folder", "audio": downloaded|skipped|failed|no_url, "has_audio"}`).

Processe um por vez; não é preciso manter contexto entre gravações — o estado vive no checkpoint e nos
arquivos.

### 4. (Opcional) Identificar o usuário

Chame `get_current_user` para carimbar o checkpoint. Guarde `id` e `nickname` para o passo 5.

### 5. Finalizar o checkpoint

```
python3 "$ENGINE" finalize --root "$ROOT" --user-id "<id>" --user-nickname "<nickname>"
```

Isso atualiza os campos de topo do checkpoint: `version`, `last_synced_at`, `last_created_at` (marca
d'água) e `user`. (Os `--user-*` são opcionais; sem eles, o usuário anterior é preservado.)

### 6. Reportar

Resuma ao usuário: quantas gravações novas foram baixadas, quantas foram puladas (já completas),
quantas falharam no áudio (`audio: failed` — serão tentadas de novo no próximo `sync`), e onde os
arquivos ficaram (`.plaud/recordings/`).

## Garantias e limites

- **Segurança:** o motor nunca grava URLs assinadas (`presigned_url`, `data_link`) no `nota.md` nem no
  checkpoint — só o `id` do Plaud. A `get_file` é chamada fresca a cada run, então a URL de áudio
  (validade de 24h) nunca vence no meio.
- **Idempotência / auto-cura:** re-rodar `sync` não duplica nada. Uma gravação só conta como completa
  quando `nota.md` existe e (o `audio.mp3` está presente **ou** a gravação não tem áudio no servidor).
  Um download que falhou é re-tentado no próximo `sync`.
- **Incremental de verdade:** só baixa o ausente/incompleto. Para reprocessar tudo, é a `sync-all`.

## Fronteiras (o que esta skill NÃO faz)

- **Não é a carga total** — ignorar o checkpoint e reprocessar tudo é a skill `sync-all`.
- **Não faz upload** nem edita/apaga nada no servidor Plaud (só leitura/download).
- **Não apaga** arquivos locais que sumiram do servidor (sem exclusão destrutiva).
- **Não baixa a transcrição polida** (`transaction_polish`) nesta versão.
