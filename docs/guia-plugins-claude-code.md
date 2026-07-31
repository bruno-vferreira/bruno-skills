# Guia Completo: Criação de Plugins para Claude Code

> Compilado a partir da documentação oficial (code.claude.com/docs, platform.claude.com/docs e spec agentskills.io) em 2026-07-30, refletindo Claude Code v2.1.200+. Recursos marcados com `v2.1.xxx+` exigem versão mínima; recursos marcados como *experimental* podem mudar.

---

## Índice

1. [Visão geral](#1-visão-geral)
2. [Estrutura de diretórios de um plugin](#2-estrutura-de-diretórios-de-um-plugin)
3. [plugin.json — schema completo](#3-pluginjson--schema-completo)
4. [marketplace.json — schema completo](#4-marketplacejson--schema-completo)
5. [Skills (SKILL.md)](#5-skills-skillmd)
6. [Slash commands](#6-slash-commands)
7. [Subagents (agents/)](#7-subagents-agents)
8. [Hooks](#8-hooks)
9. [MCP servers no plugin](#9-mcp-servers-no-plugin)
10. [Outros componentes (LSP, bin/, themes, monitors, output styles)](#10-outros-componentes)
11. [Variáveis e placeholders](#11-variáveis-e-placeholders)
12. [Settings e integração](#12-settings-e-integração)
13. [CLI e comandos de gestão de plugins](#13-cli-e-comandos-de-gestão-de-plugins)
14. [Fluxo de desenvolvimento, validação e publicação](#14-fluxo-de-desenvolvimento-validação-e-publicação)
15. [Paralelismo, background e agent teams](#15-paralelismo-background-e-agent-teams)
16. [Memória e CLAUDE.md](#16-memória-e-claudemd)
17. [Checklist do autor de plugin](#17-checklist-do-autor-de-plugin)

---

## 1. Visão geral

Um **plugin** é um pacote distribuível que estende o Claude Code com um ou mais destes componentes:

| Componente | Local padrão no plugin | O que adiciona |
|---|---|---|
| Skills | `skills/<nome>/SKILL.md` | Instruções invocáveis (`/plugin:skill`) e auto-invocáveis pelo modelo |
| Commands | `commands/*.md` | Skills em arquivo único (formato legado, ainda suportado) |
| Agents | `agents/*.md` | Subagents especializados |
| Hooks | `hooks/hooks.json` | Automações em eventos do ciclo de vida |
| MCP servers | `.mcp.json` | Ferramentas externas (stdio/http/sse/ws) |
| LSP servers | `.lsp.json` | Code intelligence por extensão de arquivo |
| Workflows | `workflows/*.js` | Scripts de orquestração multi-agente |
| Output styles | `output-styles/*.md` | Modificações do system prompt |
| Themes *(experimental)* | `themes/*.json` | Temas de cor |
| Monitors *(experimental)* | `monitors/monitors.json` | Processos de background que geram notificações |
| Executáveis | `bin/` | Binários adicionados ao PATH do Bash enquanto o plugin está ativo |
| Settings | `settings.json` | Configurações padrão do plugin |

Todos os componentes de plugin são **namespaced**: `/plugin-name:skill-name`, agent `plugin-name:agent-name`, tool MCP `mcp__plugin_<plugin>_<server>__<tool>`.

Um **marketplace** é um repositório com `.claude-plugin/marketplace.json` que cataloga plugins de várias fontes (paths locais, GitHub, git URL, git-subdir, npm).

---

## 2. Estrutura de diretórios de um plugin

```
plugin-root/
├── .claude-plugin/
│   └── plugin.json          # Manifest — ÚNICO arquivo que fica aqui dentro
├── skills/                  # Skills: <nome>/SKILL.md (+ references/, scripts/, assets/)
│   └── minha-skill/
│       ├── SKILL.md
│       ├── references/
│       └── scripts/
├── commands/                # Skills em arquivo .md plano (alternativa)
├── agents/                  # Subagents (.md); subpastas viram parte do nome
├── workflows/               # Scripts de workflow
├── output-styles/
├── themes/                  # (experimental)
├── monitors/                # (experimental) monitors.json
├── hooks/
│   └── hooks.json           # Pode haver múltiplos arquivos .json de hooks
├── .mcp.json                # MCP servers
├── .lsp.json                # LSP servers
├── bin/                     # Executáveis (PATH do Bash)
├── scripts/                 # Scripts usados por hooks/skills
├── settings.json            # Settings padrão do plugin
├── README.md
├── CHANGELOG.md
└── LICENSE
```

**Regras críticas:**

- `.claude-plugin/` contém **apenas** `plugin.json`. Componentes (`skills/`, `agents/`, `hooks/`…) ficam na **raiz do plugin**, nunca dentro de `.claude-plugin/`.
- Todos os paths no manifest são **relativos** e devem começar com `./`.
- `CLAUDE.md` na raiz do plugin **não é carregado** como contexto. Use skills para instruções que devem entrar no contexto.
- Um plugin pode ter um único `SKILL.md` na raiz (sem pasta `skills/`); o `name` do frontmatter define o nome invocável.
- O manifest é opcional: sem `plugin.json`, há auto-discovery pelos diretórios padrão.

---

## 3. plugin.json — schema completo

Único campo obrigatório: `name` (kebab-case, sem espaços — define o namespace).

```json
{
  "$schema": "https://json.schemastore.org/claude-code-plugin-manifest.json",
  "name": "meu-plugin",
  "displayName": "Meu Plugin",
  "version": "1.2.0",
  "description": "O que o plugin faz",
  "author": { "name": "Autor", "email": "a@b.com", "url": "https://github.com/autor" },
  "homepage": "https://docs.example.com",
  "repository": "https://github.com/autor/meu-plugin",
  "license": "MIT",
  "keywords": ["deploy", "ci-cd"],
  "defaultEnabled": true
}
```

### Metadados

| Campo | Tipo | Notas |
|---|---|---|
| `name` | string | **Obrigatório.** kebab-case; vira o namespace (`/meu-plugin:skill`) |
| `displayName` | string | Nome legível na UI (v2.1.143+); fallback: `name` |
| `version` | string | Semver. Se definida, **fixa** a versão — usuários só recebem update quando o campo muda. Se omitida, cada commit SHA é uma versão nova |
| `description`, `author`, `homepage`, `repository`, `license`, `keywords` | — | Metadados de catálogo |
| `defaultEnabled` | boolean | `false` = instala desabilitado (v2.1.154+). Default `true` |

Campos top-level não reconhecidos são **ignorados** (`claude plugin validate` os reporta como warnings; erros com `--strict`).

### Overrides de caminhos de componentes

| Campo | Tipo | Comportamento vs. diretório padrão |
|---|---|---|
| `skills` | string\|array | **Adiciona** ao scan padrão `skills/` |
| `commands` | string\|array | **Substitui** `commands/` |
| `agents` | string\|array | **Substitui** `agents/` |
| `workflows` | string\|array | **Substitui** `workflows/` |
| `hooks` | string\|array\|object | **Mescla** múltiplas fontes (path(s) ou config inline) |
| `mcpServers` | string\|array\|object | **Mescla** (path(s) ou config inline) |
| `outputStyles` | string\|array | **Substitui** `output-styles/` |
| `lspServers` | string\|array\|object | **Substitui** `.lsp.json` |
| `experimental.themes` | string\|array | **Substitui** `themes/` |
| `experimental.monitors` | string\|array | **Substitui** `monitors/monitors.json` |

### userConfig — configuração pelo usuário

Define opções que o usuário preenche na instalação (`/plugin` ou `--config chave=valor`):

```json
{
  "userConfig": {
    "api_token": {
      "type": "string",
      "title": "API Token",
      "description": "Token de autenticação",
      "sensitive": true,
      "required": true
    },
    "debug_mode": { "type": "boolean", "title": "Debug" },
    "max_retries": { "type": "number", "min": 1, "max": 10 },
    "config_dir": { "type": "directory", "title": "Diretório de config" },
    "cert_file": { "type": "file", "title": "Certificado" },
    "tags": { "type": "string", "multiple": true }
  }
}
```

- Tipos: `string`, `number`, `boolean`, `directory`, `file`. Extras: `sensitive` (vai para o keychain, mascarado), `required`, `default`, `multiple` (array de strings), `min`/`max` (number).
- **Acesso aos valores:** em skills/agents via `${user_config.CHAVE}` (só não-sensíveis); em hooks/monitors/MCP via env var `CLAUDE_PLUGIN_OPTION_<CHAVE>` (maiúsculas). Em hooks com shell form são rejeitados — use exec form com `args`.
- Valores ficam em `pluginConfigs` no settings do usuário (sensíveis vão para o keychain).

### Outros campos

```json
{
  "dependencies": [
    "outro-plugin",
    { "name": "secrets-vault", "version": "~2.1.0" }
  ],
  "channels": [
    { "server": "telegram", "userConfig": { "bot_token": { "type": "string", "sensitive": true } } }
  ]
}
```

- `dependencies`: outros plugins requeridos (string ou objeto com constraint semver).
- `channels`: canais de comunicação ligados a um MCP server declarado (o `server` deve corresponder a uma chave em `mcpServers`).

---

## 4. marketplace.json — schema completo

Fica **sempre** em `.claude-plugin/marketplace.json` na raiz do repositório do marketplace.

```json
{
  "$schema": "https://json.schemastore.org/claude-code-marketplace-manifest.json",
  "name": "meu-marketplace",
  "description": "Descrição do marketplace",
  "version": "1.0",
  "owner": { "name": "Mantenedor", "email": "x@y.com", "url": "https://github.com/org" },
  "metadata": { "pluginRoot": "./plugins" },
  "renames": { "nome-antigo": "nome-novo", "removido": null },
  "allowCrossMarketplaceDependenciesOn": [
    { "source": "github", "repo": "org/outro-marketplace" }
  ],
  "plugins": [
    {
      "name": "meu-plugin",
      "source": "./plugins/meu-plugin",
      "description": "...",
      "version": "2.1.0",
      "category": "productivity",
      "tags": ["tag1"],
      "strict": true,
      "defaultEnabled": true
    }
  ]
}
```

**Obrigatórios:** `name` (kebab-case; usuários registram um marketplace por nome), `owner` (`name` obrigatório), `plugins` (array).

**Opcionais:** `description`, `version`, `metadata.pluginRoot` (base para sources relativas), `renames` (migração automática de nomes, v2.1.193+), `allowCrossMarketplaceDependenciesOn` (allowlist de dependências cross-marketplace).

### Entradas de plugin

Obrigatórios por entrada: `name` e `source`. Opcionais: os mesmos metadados do plugin.json (`displayName`, `version`, `author`, `license`, `keywords`…) mais `category`, `tags`, `relevance` (v2.1.152+, sinais de sugestão), `strict`, `defaultEnabled`, e overrides de componentes (`skills`, `commands`, `agents`, `hooks`, `mcpServers`, `lspServers`).

### Tipos de source

```json
"source": "./plugins/local-plugin"

"source": { "source": "github", "repo": "owner/repo", "ref": "main", "sha": "a1b2c3…" }

"source": { "source": "url", "url": "https://gitlab.com/team/plugin.git", "ref": "v2.0.0" }

"source": { "source": "git-subdir", "url": "github.com/org/monorepo", "path": "tools/claude-plugin", "sha": "…" }

"source": { "source": "npm", "package": "@acme/claude-plugin", "version": "^2.0.0", "registry": "https://npm.example.com" }
```

Paths relativos devem começar com `./` e resolvem contra a raiz do marketplace (ou `metadata.pluginRoot`). `git-subdir` usa sparse clone (bom para monorepos).

### strict mode

- `strict: true` (default): o `plugin.json` do plugin é a autoridade; a entrada do marketplace **suplementa** (mescla).
- `strict: false`: a entrada do marketplace é a definição **completa**; se o plugin também tiver `plugin.json`, é conflito e falha. Útil para curadoria/reestruturação por quem opera o marketplace.

---

## 5. Skills (SKILL.md)

### Estrutura e progressive disclosure

```
minha-skill/
├── SKILL.md          # obrigatório: frontmatter YAML + instruções
├── references/       # docs de referência, carregadas sob demanda
├── scripts/          # código executável (a saída é que consome tokens)
└── assets/           # templates, dados estáticos
```

Carregamento em 3 níveis:

| Nível | Quando | Custo |
|---|---|---|
| 1 — Metadata (`name` + `description`) | Sempre, no startup | ~100 tokens/skill |
| 2 — Corpo do SKILL.md | Quando invocada | < 5.000 tokens recomendado |
| 3 — references/scripts/assets | Sob demanda (Read/execução) | Zero até acessar |

O nome da pasta deve corresponder ao `name` do frontmatter.

### Frontmatter — campos da spec (agentskills.io)

| Campo | Regras |
|---|---|
| `name` | **Obrigatório.** ≤64 chars; só `a-z`, `0-9`, `-`; sem `--`, sem hífen no início/fim; sem "anthropic"/"claude" |
| `description` | **Obrigatório.** ≤1024 chars; sem tags XML; terceira pessoa; deve dizer **o que faz** e **quando usar**, com palavras-gatilho |
| `license` | Identificador/texto de licença |
| `compatibility` | ≤500 chars; requisitos de ambiente (raro precisar) |
| `metadata` | Mapa string→string livre (author, version, category…) |
| `allowed-tools` | Ferramentas pré-aprovadas (experimental na spec; expandido no Claude Code) |

### Frontmatter — extensões do Claude Code

| Campo | Default | Efeito |
|---|---|---|
| `disable-model-invocation` | `false` | `true` = só o usuário invoca (`/nome`); sai do listing que o modelo vê. Use para ações com efeito colateral (deploy, commit) |
| `user-invocable` | `true` | `false` = some do menu `/`; só o modelo invoca. Use para contexto de background |
| `when_to_use` | — | Complemento da description no listing (description + when_to_use truncados em 1536 chars) |
| `argument-hint` | — | Dica no autocomplete, ex. `[issue-number]` |
| `arguments` | — | Nomes posicionais para substituição `$nome` (ex.: `arguments: issue branch`) |
| `allowed-tools` | — | Pré-aprova tools **só no turno da invocação** (expira no próximo input do usuário). Ex.: `Bash(git add *) Bash(git commit *)` |
| `disallowed-tools` | — | Remove tools do pool enquanto a skill está ativa |
| `model` | inherit | Override de modelo pelo resto do turno (`sonnet`, `opus`, `haiku`, ID completo, `inherit`) |
| `effort` | herda | `low` \| `medium` \| `high` \| `xhigh` \| `max` |
| `context` | inline | `fork` = roda em subagent isolado (sem histórico da conversa) |
| `agent` | `general-purpose` | Tipo de subagent com `context: fork` (`Explore`, `Plan`, custom) |
| `background` | `true` | Com `context: fork`: `false` = espera o resultado no mesmo turno (v2.1.218+) |
| `hooks` | — | Hooks com escopo do ciclo de vida da skill |
| `paths` | — | Globs que limitam a ativação automática (ex.: `"*.py,*.ts"`) |
| `shell` | `bash` | `bash` \| `powershell` para injeção dinâmica |

### Corpo — recursos

```markdown
---
name: pr-summary
description: Resume o PR atual. Use quando o usuário pedir resumo de PR.
allowed-tools: Bash(gh *)
---

## Contexto
- Diff: !`gh pr diff`
- Args: $ARGUMENTS ($0, $1… posicionais; $issue se declarado em `arguments`)
- Arquivo: @docs/template.md

Resuma este PR…
```

- **Substituições:** `$ARGUMENTS`, `$ARGUMENTS[N]`, `$N`, `$nome`; env: `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}`, `${CLAUDE_SKILL_DIR}`, `${CLAUDE_PROJECT_DIR}`.
- **Injeção dinâmica:** `` !`cmd` `` inline ou bloco ```` ```! ```` multi-linha — executa **antes** de o Claude ver o conteúdo; requer `allowed-tools: Bash(...)`; o output não é re-escaneado. Pode ser desativado globalmente com `disableSkillShellExecution: true`.
- **`@path`** referencia arquivos; **`ultrathink`** no corpo ativa raciocínio profundo.
- Argumentos multi-palavra exigem aspas; `\$` escapa o literal.

### Localização e precedência

| Escopo | Caminho |
|---|---|
| Enterprise (managed) | settings gerenciados — precedência mais alta |
| Pessoal | `~/.claude/skills/<nome>/SKILL.md` |
| Projeto | `.claude/skills/<nome>/SKILL.md` (aninhados em subdirs viram `/subdir:nome`) |
| Plugin | `<plugin>/skills/<nome>/SKILL.md` → `/plugin:nome` (namespaced) |
| Bundled | skills embutidas (`/code-review`, `/doctor`…) — precedência mais baixa |

Em conflito de nome: enterprise > pessoal > projeto > plugin > bundled. O atalho sem prefixo (`/nome`) funciona se não houver conflito.

### Ciclo de vida e budget

- O conteúdo invocado entra como mensagem e **fica no contexto** o resto da sessão; re-invocação idêntica não duplica.
- Listing de skills para o modelo: budget de **1% da janela de contexto** (`skillListingBudgetFraction` ou `SLASH_COMMAND_TOOL_CHAR_BUDGET`).
- Compactação: skills recentes mantidas com até 5.000 tokens cada, budget compartilhado de 25.000 tokens. Se uma skill "parar de funcionar" depois de compactar, re-invoque.
- `allowed-tools` da skill expira no próximo input do usuário.

### Boas práticas de autoria

- **name** em gerúndio ou verbo-ação (`processing-pdfs`, `analyze-spreadsheets`); nunca genérico (`helper`, `utils`).
- **description** = o que faz + quando usar + palavras-gatilho, em terceira pessoa.
- Corpo **< 500 linhas**; acima disso, dividir em `references/` (1 nível de profundidade apenas — evite cadeias `SKILL.md → a.md → b.md`).
- Scripts para operações frágeis/determinísticas (parsing, validação, deploy); deixe claro se o Claude deve **executar** ou **ler** o script.
- Exemplos input/output ensinam estilo melhor que descrições.
- Organização por domínio: `references/finance.md`, `references/sales.md` — só o domínio consultado consome tokens.

---

## 6. Slash commands

Commands (`commands/*.md`) e skills são **funcionalmente idênticos** — commands são o formato legado de arquivo único; skills (diretório) são o recomendado e suportam arquivos auxiliares. O frontmatter é o mesmo da seção 5.

- Projeto: `.claude/commands/deploy.md` → `/deploy`
- Pessoal: `~/.claude/commands/…`
- Plugin: `commands/cmd.md` → `/plugin-name:cmd`

O modelo invoca skills/commands via **Skill tool** (a description de cada um fica no contexto; `disable-model-invocation: true` a remove do listing). Built-ins como `/compact` não são invocáveis pelo modelo.

Built-ins úteis para autores: `/plugin`, `/reload-plugins`, `/agents`, `/hooks`, `/memory`, `/config`, `/doctor`, `/debug`, `/context`.

---

## 7. Subagents (agents/)

Arquivo markdown: frontmatter + corpo (o corpo é o **system prompt** do subagent).

### Localização e precedência

Managed > `--agents` (CLI, só a sessão) > `.claude/agents/` (projeto, recursivo) > `~/.claude/agents/` (pessoal) > plugin `agents/`. File watcher aplica mudanças sem restart (exceto o primeiro arquivo de um diretório `agents/` novo). Em plugin, subpastas entram no nome: `meu-plugin/agents/review/security.md` → `meu-plugin:review:security`.

### Frontmatter completo

```yaml
---
name: code-reviewer            # OBRIGATÓRIO: lowercase + hífens
description: Expert code review specialist. Use proactively for code review.  # OBRIGATÓRIO
tools: Read, Grep, Glob, Bash  # allowlist; omitido = herda todas
disallowedTools: Write, Edit   # denylist; mcp__* remove todos MCP
model: sonnet                  # sonnet|opus|haiku|<id>|inherit (default inherit)
permissionMode: default        # default|acceptEdits|auto|dontAsk|bypassPermissions|plan (ignorado em plugin subagents)
maxTurns: 30                   # default: sem limite
background: false              # true = sempre em background
effort: high                   # low|medium|high|xhigh|max
isolation: worktree            # worktree isolado (branch a partir do default branch)
skills: [minha-skill]          # pré-carrega conteúdo COMPLETO das skills
mcpServers:                    # por nome (já configurado) ou definição inline
  - github
memory: project                # user|project|local — memória persistente do agent
color: cyan                    # cor na UI
hooks:                         # hooks com escopo deste subagent
  PreToolUse:
    - matcher: "Bash"
      hooks: [{ type: command, command: "./scripts/validate.sh" }]
---
You are a senior code reviewer…
```

Notas:

- `tools: Agent(worker, researcher)` restringe quais subagents ele pode spawnar; `mcp__github` = todas as tools daquele server.
- Ordem de resolução de `model`: `CLAUDE_CODE_SUBAGENT_MODEL` → parâmetro por invocação → frontmatter → modelo da sessão.
- `memory`: `user` = `~/.claude/agent-memory/<name>/`; `project` = `.claude/agent-memory/<name>/`; `local` = `.claude/agent-memory-local/<name>/`.
- Hooks `Stop` no frontmatter viram `SubagentStop`. Em plugin subagents, `hooks` e `permissionMode` são ignorados (v2.1.200+).
- Parent em `bypassPermissions`/`acceptEdits` força o subagent a herdar o modo.

### Invocação

- **Automática:** o Claude delega com base na `description` ("use proactively" ajuda).
- **Explícita:** `@agent-nome`, linguagem natural, `claude --agent nome` (sessão inteira como o agent), ou setting `"agent": "nome"`.

### Built-ins e o que um subagent carrega

- Built-ins: `Explore` e `Plan` (read-only, **pulam CLAUDE.md e git status**), `general-purpose` (todas as tools). Desabilitar: `permissions.deny: ["Agent(Explore)"]` ou `CLAUDE_CODE_DISABLE_EXPLORE_PLAN_AGENTS=1`.
- Um subagent normal recebe: system prompt próprio, mensagem de delegação, hierarquia de CLAUDE.md, git status, skills pré-carregadas. Um **fork** recebe o histórico completo do pai (e reusa o prompt cache).

### Limites de paralelismo

| Limite | Default | Env var |
|---|---|---|
| Profundidade de aninhamento | 3 | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` |
| Total por sessão | 200 | `CLAUDE_CODE_MAX_SUBAGENTS_PER_SESSION` |
| Concorrentes | 20 | `CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS` |

Subagents em background têm pool de tools reduzido; forks herdam o pool completo. Ferramentas nunca disponíveis em subagents: `AskUserQuestion`, `EnterPlanMode`, `Workflow`, `ScheduleWakeup`, entre outras. Um subagent terminado pode ser **retomado** via SendMessage (transcripts em `~/.claude/projects/<proj>/<sessão>/subagents/`).

---

## 8. Hooks

### Configuração

Três níveis de aninhamento, em `settings.json` (user/projeto/local/managed), `hooks/hooks.json` de plugin, ou frontmatter de skill/agent:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Edit",
        "hooks": [
          {
            "type": "command",
            "if": "Bash(git *)",
            "command": "${CLAUDE_PROJECT_DIR}/.claude/hooks/check.sh",
            "timeout": 30,
            "statusMessage": "Validando…"
          }
        ]
      }
    ]
  }
}
```

### Eventos (todos)

**Sessão:** `SessionStart` (matcher: `startup|resume|clear|compact|fork`), `Setup` (`init|maintenance`), `SessionEnd` (`clear|logout|prompt_input_exit|…`).

**Turno:** `UserPromptSubmit`*, `UserPromptExpansion`* (matcher = nome do comando), `Stop`*, `StopFailure` (matcher = tipo de erro: `rate_limit|overloaded|…`), `PostToolBatch`, `MessageDisplay`.

**Tool:** `PreToolUse`*, `PermissionRequest`*, `PermissionDenied` (`{retry: true}` permite retry), `PostToolUse`, `PostToolUseFailure`.

**Diversos:** `Notification` (matcher = tipo: `permission_prompt|idle_prompt|agent_needs_input|…`), `SubagentStart`/`SubagentStop` (matcher = tipo/nome do agent), `TaskCreated`*/`TaskCompleted`* (exit 2 bloqueia), `TeammateIdle`* (exit 2 mantém trabalhando), `InstructionsLoaded`, `ConfigChange`* (matcher = fonte), `CwdChanged`, `FileChanged` (matcher = filenames literais separados por `|`), `WorktreeCreate`/`WorktreeRemove`, `PreCompact`/`PostCompact` (`manual|auto`), `Elicitation`/`ElicitationResult` (matcher = MCP server).

\* = pode bloquear a ação.

### Matchers

- `"*"`, vazio ou omitido = tudo. Strings exatas (`Bash`, `Edit|Write` — `|` e `,` intercambiáveis v2.1.191+). Regex (`mcp__.*`, `^Bash$`).
- Campo `if` (só em eventos de tool): filtra por tool + argumentos com sintaxe de permission rules — `"if": "Bash(git *)"` checa cada subcomando, inclusive dentro de `$()`/backticks (best-effort, falha aberta).
- MCP: `mcp__<server>__<tool>`; de plugin: `mcp__plugin_<plugin>_<server>__<tool>`.

### Tipos de handler

| type | O que faz | Timeout default |
|---|---|---|
| `command` | Executa shell (shell form) ou binário direto (exec form: `command` + `args`, v2.1.210+, evita quoting/injeção) | 600s (30s em UserPromptSubmit, 10s em MessageDisplay) |
| `http` | POST do JSON do evento para `url` (com `headers` e `allowedEnvVars` para interpolar `$VAR`) | 600s |
| `mcp_tool` | Chama `toolName` em `serverName` já conectado, com `arguments` | 600s |
| `prompt` | Avaliação single-turn por LLM (Haiku por default; `model` opcional); responde `{"ok": true}` ou `{"ok": false, "reason": "…"}`; `continueOnBlock: true` devolve a razão ao Claude | 30s |
| `agent` *(experimental)* | Subagent multi-turn com tools (até 50 turnos); `$ARGUMENTS` no prompt recebe o JSON do evento | 60s |

`SessionEnd` tem budget total de 1,5s (elevável até 60s via `timeout`).

### Entrada (stdin)

Campos comuns: `session_id`, `prompt_id`, `transcript_path`, `cwd`, `permission_mode`, `hook_event_name`, `agent_id`, `agent_type`. Específicos: `tool_name` + `tool_input` (eventos de tool; `tool_response` em PostToolUse), `prompt` (UserPromptSubmit), `source` (SessionStart/ConfigChange), `trigger` (Setup/PreCompact), `stop_hook_active` (Stop — cheque para evitar loop; cap de 8 bloqueios consecutivos, `CLAUDE_CODE_STOP_HOOK_BLOCK_CAP`), `error_type` (StopFailure), `file_path`/`timestamp` (FileChanged/ConfigChange), `old_cwd`/`new_cwd` (CwdChanged).

### Saída

**Exit codes:** `0` = sucesso (stdout JSON é processado; em UserPromptSubmit/SessionStart, texto puro vira contexto). `2` = **bloqueia** (stderr vira feedback ao Claude) — só nos eventos bloqueáveis. Outro = erro não-bloqueante.

**JSON estruturado (exit 0):**

```json
{
  "continue": true,
  "suppressOutput": false,
  "systemMessage": "aviso",
  "decision": "block",
  "reason": "por quê",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "texto injetado como system reminder",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "…",
    "updatedInput": { "command": "comando reescrito" }
  }
}
```

- `PreToolUse`: `permissionDecision` (`allow` pula o prompt; `deny` cancela; `ask` pergunta; `defer` para SDK) + `updatedInput` reescreve o input (só um hook deve fazê-lo).
- `PermissionRequest`: `hookSpecificOutput.decision.behavior` (`allow|deny|ask`) + `updatedPermissions`.
- `PostToolUse`/`Stop`: `decision: "block"` top-level + `reason`.
- `UserPromptSubmit`: `additionalContext` e/ou `decision: "block"`.

**Execução:** todos os hooks que casam rodam **em paralelo**; comandos idênticos são deduplicados; em PreToolUse vence a resposta mais restritiva (`deny` > `defer` > `ask` > `allow`); `additionalContext` de todos é agregado.

### Hooks em plugins

`hooks/hooks.json` com a mesma estrutura, usando `${CLAUDE_PLUGIN_ROOT}` / `${CLAUDE_PLUGIN_DATA}`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          { "type": "command", "command": ["${CLAUDE_PLUGIN_ROOT}/scripts/format.sh", "--strict"] }
        ]
      }
    ]
  }
}
```

São **mesclados** com os hooks do usuário quando o plugin está habilitado; não podem ser desabilitados individualmente (desabilite o plugin). Prefira **exec form** (`command` + `args`) para paths com placeholder. `/hooks` mostra tudo configurado (read-only); `disableAllHooks: true` desliga tudo (exceto managed).

**Env vars nos hooks:** `CLAUDE_PROJECT_DIR` (todos), `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PLUGIN_DATA` (plugins), `CLAUDE_ENV_FILE` (SessionStart/CwdChanged — escreva `export VAR=...` para valer em todo Bash seguinte, ex.: `direnv export bash > "$CLAUDE_ENV_FILE"`).

**Segurança:** hooks rodam com as permissões do usuário, sem TTY (`terminalSequence` no JSON para notificações); shell form é vulnerável a injection — use exec form; HTTP interpola só o que estiver em `allowedEnvVars`.

---

## 9. MCP servers no plugin

`.mcp.json` na raiz do plugin (ou inline em `plugin.json` via `mcpServers`):

```json
{
  "mcpServers": {
    "database-tools": {
      "type": "stdio",
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": { "DB_PATH": "${CLAUDE_PLUGIN_DATA}/data" },
      "timeout": 600000
    },
    "api": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": { "Authorization": "Bearer ${API_KEY}" },
      "oauth": { "scopes": "read write" }
    }
  }
}
```

- **Transportes:** `stdio` (local: `command`, `args`, `env`), `http` (recomendado remoto: `url`, `headers`, `headersHelper`, `oauth`), `sse` (deprecated em favor de http), `ws`. Comuns: `timeout` (ms), `alwaysLoad`.
- **Expansão de variáveis** em `command`, `args`, `env`, `url`, `headers`: `${VAR}`, `${VAR:-default}`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_PROJECT_DIR}`. Var indefinida sem default → warning e literal.
- **OAuth:** dynamic client registration automático (RFC 9728/8414) ou `oauth.clientId`/`callbackPort`/`scopes`; `claude mcp login <server>`. `headersHelper` = script que imprime JSON de headers (recebe `CLAUDE_CODE_MCP_SERVER_NAME`, `CLAUDE_CODE_MCP_SERVER_URL`).
- **Nome das tools:** `mcp__plugin_<plugin>_<server>__<tool>` — use em permissions, `allowed-tools`, matchers de hooks.
- Servers do plugin iniciam quando o plugin é habilitado. Env vars relevantes: `MCP_TIMEOUT`, `MCP_TOOL_TIMEOUT`, `MAX_MCP_OUTPUT_TOKENS` (default 25000).

Fora de plugins, os escopos MCP são: `local` (default, `~/.claude.json`), `project` (`.mcp.json` versionado; aprovação via `enableAllProjectMcpServers`/`enabledMcpjsonServers`), `user`. CLI: `claude mcp add|list|get|remove|login|logout|reset-project-choices`.

---

## 10. Outros componentes

### LSP (`.lsp.json`)

```json
{ "lspServers": { "python": { "command": "pylance", "extensionToLanguage": { ".py": "python" } } } }
```

Fornece code intelligence; scoped por extensão (se dois plugins declaram a mesma extensão, o primeiro ganha). Status em `/plugin` → LSP servers.

### bin/

Executáveis adicionados ao **PATH do Bash** enquanto o plugin está habilitado; invocáveis como comando puro (`meu-tool --help`).

### Output styles (`output-styles/*.md`)

```markdown
---
name: "Meu Estilo"
description: "…"
keep-coding-instructions: true   # mantém instruções de engenharia do prompt padrão (default false)
force-for-plugin: false          # true = aplica automaticamente quando o plugin é habilitado
---
Instruções adicionadas ao system prompt.
```

Aparecem como `plugin-name:estilo` no seletor. Locais fora de plugin: `~/.claude/output-styles/`, `.claude/output-styles/`. Mudança de estilo requer nova sessão/`/clear`.

### Themes (experimental)

`themes/*.json` → aparecem no `/theme` picker como `custom:plugin-name:slug`.

### Monitors (experimental)

`monitors/monitors.json`:

```json
[{ "name": "error-log", "command": "tail -F ./logs/error.log", "description": "Log de erros" }]
```

Iniciam com o plugin; cada linha de stdout vira notificação; aparecem no task panel. Não têm acesso a `CLAUDE_PLUGIN_OPTION_*` via command — leiam de arquivo de config.

### settings.json do plugin

Configurações padrão fornecidas pelo plugin (ex.: permissions, statusLine).

---

## 11. Variáveis e placeholders

| Variável | Resolve para | Onde usar |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | Diretório de instalação do plugin (**efêmero** — muda a cada update; versão antiga limpa em ~2 semanas) | Conteúdo de skills/agents, hooks, MCP (`command`, `args`, `env`, `url`, `headers`), LSP |
| `${CLAUDE_PLUGIN_DATA}` | `~/.claude/plugins/data/<id>/` — **persiste** entre updates | node_modules/venv, caches, estado |
| `${CLAUDE_PROJECT_DIR}` | Raiz do projeto (estável entre worktrees) | Hooks, MCP, allowed-tools |
| `${CLAUDE_SKILL_DIR}` | Diretório do SKILL.md | Corpo de skills, allowed-tools |
| `${CLAUDE_SESSION_ID}`, `${CLAUDE_EFFORT}` | ID da sessão / nível de esforço | Corpo de skills |
| `${user_config.CHAVE}` | Valor de userConfig (não-sensível) | Skills e agents |
| `CLAUDE_PLUGIN_OPTION_<CHAVE>` | Valor de userConfig como env var | Hooks (exec form), MCP |

Padrão comum — instalar dependências uma vez em `SessionStart` comparando `package.json` do ROOT com o do DATA e rodando `npm install` no DATA; depois `NODE_PATH: ${CLAUDE_PLUGIN_DATA}/node_modules` no MCP server.

---

## 12. Settings e integração

Precedência (maior → menor): **managed** → `--settings` CLI → `~/.claude/settings.json` (user) → `.claude/settings.json` (projeto) → `.claude/settings.local.json` (local, auto-gitignored). Settings recarregam automaticamente (exceto `model` e `outputStyle`); o hook `ConfigChange` dispara a cada mudança.

Chaves relevantes para plugins:

```json
{
  "enabledPlugins": { "formatter@meu-marketplace": true, "linter@official": false },
  "extraKnownMarketplaces": {
    "company-tools": { "source": { "source": "github", "repo": "acme/claude-plugins" } },
    "local-dev": { "source": { "source": "directory", "path": "./local-plugins" } }
  },
  "pluginConfigs": { "meu-plugin": { "options": { "api_endpoint": "https://…" } } },
  "permissions": {
    "allow": ["Bash(npm run *)", "mcp__plugin_meu-plugin_db__*"],
    "deny": ["Bash(rm -rf *)"],
    "ask": []
  },
  "hooks": {},
  "statusLine": { "type": "command", "command": "~/.claude/statusline.sh" },
  "env": { "NODE_ENV": "development" }
}
```

Controles de admin (managed): `strictKnownMarketplaces` (allowlist; `[]` = lockdown), `blockedMarketplaces`, `allowedMcpServers`/`deniedMcpServers`, `disableSideloadFlags` (bloqueia `--plugin-dir`/`--mcp-config`).

**Statusline** (útil para plugins fornecerem default): script recebe JSON rico no stdin (model, workspace, git, cost, `context_window.used_percentage`, rate_limits, vim mode, PR status…) e imprime linhas; `refreshInterval` mínimo 1s; debounce de 300ms.

---

## 13. CLI e comandos de gestão de plugins

```bash
claude plugin init <nome> [--with skills agents hooks mcp lsp output-style channel] [--description ... --author ...]
claude plugin install <plugin>[@marketplace] [--scope user|project|local] [--config chave=valor]
claude plugin uninstall <plugin> [--keep-data] [--prune -y]
claude plugin enable|disable <plugin> [--scope ...]   # disable aceita --all
claude plugin update <plugin> [--scope user|project|local|managed]
claude plugin list [--json] [--available]
claude plugin details <nome>          # inventário + custo de tokens projetado
claude plugin validate <path> [--strict]
claude plugin prune [--dry-run -y]
claude plugin tag [path] [--push --dry-run -m "msg %s"]   # tag <nome>--v<versão>

claude plugin marketplace add <source> [--scope ...] [--sparse dirs...]
claude plugin marketplace list [--json]
claude plugin marketplace remove <nome> [--scope ...]
claude plugin marketplace update [nome]
```

Na sessão interativa: `/plugin` (UI de gestão), `/plugin install x@y`, `/plugin marketplace add owner/repo`, `/plugin list --enabled`, `/reload-plugins`.

Fontes aceitas em `marketplace add`: `owner/repo` (GitHub, `@ref` para branch/tag), git URL (`#ref`), URL de `marketplace.json`, path local.

Desinstalar do último escopo apaga `${CLAUDE_PLUGIN_DATA}` (preserve com `--keep-data`).

---

## 14. Fluxo de desenvolvimento, validação e publicação

### Desenvolvimento local

**Opção A — `--plugin-dir` (mais direto):**

```bash
claude --plugin-dir ./meu-plugin      # ou apontar para um marketplace local
# na sessão: /reload-plugins → /meu-plugin:minha-skill
```

**Opção B — `claude plugin init`:** cria scaffold em `~/.claude/skills/<nome>/`, auto-carregado como `<nome>@skills-dir`.

**Opção C — marketplace local:** estrutura `marketplace/.claude-plugin/marketplace.json` + `plugins/...`; `/plugin marketplace add ./meu-marketplace` → `/plugin install meu-plugin@meu-marketplace`. Iterar com `/plugin marketplace update` + `/plugin update` + `/reload-plugins`.

Skills recarregam ao vivo; outros componentes precisam de `/reload-plugins`. MCP connections sobrevivem ao reload.

### Validação e debug

- `claude plugin validate ./meu-plugin [--strict]` — valida manifest e estrutura.
- `claude --debug` ou `/debug` — mostra carregamento de plugin, registro de skills/agents/hooks, init de MCP.
- Problemas comuns: componentes dentro de `.claude-plugin/` (errado), script de hook sem `chmod +x`, path absoluto em vez de `./`, MCP sem `${CLAUDE_PLUGIN_ROOT}`.

### Versionamento e publicação

- Sem `version` no manifest: cada commit = update automático (bom para dev). Com `version`: usuários só atualizam quando o campo muda (semver).
- Canais de release: marketplaces distintos apontando para `ref: stable` / `ref: latest`.
- `claude plugin tag --push` cria tag git `<plugin>--v<versão>`.
- Submissão ao diretório oficial: platform.claude.com/plugins/submit (Console) ou claude.ai admin (Team/Enterprise) → community marketplace `@claude-community`.

---

## 15. Paralelismo, background e agent teams

### Background tasks (Bash)

- `Ctrl+B` envia um comando em execução para background (2× em tmux); ou peça "run in background". Prefixo `!` roda shell direto com output no contexto.
- Output vai para arquivo + task ID; o Claude lê com Read. Auto-terminados em >5GB de output ou ~30min idle sob pressão de memória. Desabilitar: `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`.
- Uso típico: dev servers, builds, test runners.
- `Ctrl+T` = checklist de tarefas do Claude; `/tasks` = tarefas em background; `Ctrl+X Ctrl+K` = parar todos os subagents em background.

### Subagents em paralelo

- Rodam na mesma sessão, cada um com contexto próprio; comunicação **one-way** (só reportam de volta). Múltiplos podem rodar simultaneamente (limites na seção 7).
- Desde v2.1.198 o default tende a background: o main continua e o resultado volta como notificação em turno posterior; prompts de permissão aparecem na sessão principal.

### Agent teams (teammates) — experimental

Habilitar: `"env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" }`.

- **Lead** (sessão principal) spawna **teammates** — sessões independentes com contexto próprio que se comunicam diretamente (mailbox em `~/.claude/teams/<team>/inboxes/`) e compartilham task list (`~/.claude/tasks/<team>/`) com file locking e dependências automáticas.
- Display: `teammateMode` = `in-process` (default) | `auto` | `tmux` | `iterm2` (split panes exigem tmux/iTerm2; não funcionam no terminal integrado do VS Code).
- Plan approval: teammate fica read-only até o lead aprovar o plano. Hooks: `TeammateIdle` (exit 2 mantém trabalhando), `TaskCreated`/`TaskCompleted` (exit 2 bloqueia).
- Teammates podem usar definições de subagent como tipo (honram `tools` e `model`; ignoram `skills`, `mcpServers`, `permissionMode`). Herdam o permission mode do lead; não herdam o histórico da conversa (inclua contexto no spawn prompt).
- Limitações: 1 team por sessão; sem teams aninhados; `/resume` não restaura teammates in-process; custo de tokens escala linearmente. Boas práticas: 3–5 teammates, 5–6 tasks por teammate, isolar arquivos por teammate.
- Diferença para subagents: subagents reportam ao main (one-way); teammates conversam entre si (two-way).

### Git worktrees

- `claude --worktree nome` cria sessão em worktree isolado (`.claude/worktrees/`) — várias sessões paralelas sem conflito de edição. Requer ≥1 commit.
- `claude agents` = interface full-screen para despachar/monitorar background agents (cada um auto-move para worktree antes de editar).
- `.worktreeinclude` lista paths (globs) sempre copiados para o worktree. Hooks `WorktreeCreate`/`WorktreeRemove` customizam o comportamento (suporte a VCS não-git).

### Headless / CI

```bash
claude -p "corrija o bug em auth.py" --output-format json | jq '.result'
claude -p "…" --bare                      # sem hooks, skills, plugins, MCP, CLAUDE.md (CI consistente)
claude -p "…" --output-format stream-json --include-partial-messages
claude -p "…" --continue | --resume SESSION_ID
claude -p "…" --allowedTools "Bash,Read,Edit" --permission-mode acceptEdits
claude -p "…" --append-system-prompt "You are a security engineer."   # ou --system-prompt / --system-prompt-file
cat erro.txt | claude -p 'explique a causa raiz'    # stdin até 10MB
claude -p "…" --json-schema '{"type":"object",…}'   # saída estruturada
```

- `CLAUDE_CODE_FORWARD_SUBAGENT_TEXT=1` (ou `--forward-subagent-text`) emite texto/thinking dos subagents no stream (v2.1.211+).
- Background tasks no `-p`: grace de ~5s; subagents/workflows aguardam (teto 10min, `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS`).
- Agent SDK: `claude-agent-sdk` (Python) / `@anthropic-ai/claude-agent-sdk` (TS) — harness completo self-hosted.

---

## 16. Memória e CLAUDE.md

- Hierarquia: managed → `~/.claude/CLAUDE.md` → `./CLAUDE.md` ou `.claude/CLAUDE.md` → `CLAUDE.local.md` → `CLAUDE.md` aninhados em subdirs (carregados sob demanda). Alvo: ≤200 linhas por arquivo.
- Imports com `@path/to/file.md` (até 4 níveis; ignorados dentro de code blocks; `` `@x` `` em backticks não importa; imports externos pedem aprovação).
- `.claude/rules/*.md` com frontmatter `paths: ["src/api/**/*.ts"]` = regras carregadas só quando arquivos casam (melhor que inflar o CLAUDE.md).
- Auto-memory: `~/.claude/projects/<proj>/memory/` — `MEMORY.md` (primeiras 200 linhas/25KB carregadas por sessão) + topic files sob demanda. Toggle com `/memory` ou `autoMemoryEnabled`.
- **Para plugins:** o CLAUDE.md do plugin não é carregado — instruções persistentes devem virar **skills** (ex.: `user-invocable: false` para contexto que só o modelo consome).

---

## 17. Checklist do autor de plugin

**Estrutura**
- [ ] `plugin.json` só com `.claude-plugin/`; componentes na raiz
- [ ] Paths relativos com `./`; nada de paths absolutos ou `\` do Windows
- [ ] `claude plugin validate --strict` passa

**Skills**
- [ ] `name` kebab-case ≤64; `description` ≤1024 em 3ª pessoa com o-que + quando + gatilhos
- [ ] Corpo <500 linhas; detalhes em `references/` (1 nível); scripts para operações frágeis
- [ ] `disable-model-invocation: true` em ações com efeito colateral

**Hooks/MCP**
- [ ] `${CLAUDE_PLUGIN_ROOT}` em todos os paths; estado persistente em `${CLAUDE_PLUGIN_DATA}`
- [ ] Exec form (`command` + `args`) em vez de shell form quando houver placeholders/input externo
- [ ] Scripts com `chmod +x`; timeouts conservadores; `stop_hook_active` checado em Stop hooks

**Distribuição**
- [ ] `version` semver definida (ou consciente de que commit SHA = update automático)
- [ ] `marketplace.json` com `owner` e sources corretas; testado com marketplace local
- [ ] README + CHANGELOG; `claude plugin details` para conferir custo de tokens
- [ ] Testado com `--plugin-dir` + `/reload-plugins` e instalado de verdade via marketplace

---

### Fontes

- Plugins: code.claude.com/docs/en/plugins, /plugins-reference, /plugin-marketplaces
- Skills: code.claude.com/docs/en/skills; platform.claude.com/docs/en/agents-and-tools/agent-skills (overview, best practices); agentskills.io/specification
- Hooks: code.claude.com/docs/en/hooks-guide, /hooks
- Commands/Subagents: code.claude.com/docs/en/slash-commands, /sub-agents
- Settings/MCP/Memory/Statusline: code.claude.com/docs/en/settings, /mcp, /memory, /statusline, /output-styles
- Paralelismo/Teams/Headless: code.claude.com/docs/en/agent-teams, /interactive-mode, /common-workflows, /cli-reference
