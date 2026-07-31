# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A Claude Code **plugin marketplace** of Agent Skills (the `SKILL.md` format from agentskills.io). `.claude-plugin/marketplace.json` lists every plugin; each plugin lives in `plugins/<name>/` with its own `.claude-plugin/plugin.json` manifest and one or more skills under `skills/<skill-name>/SKILL.md`. `catalog/index.json` is a **generated** machine-readable catalog — never edit it by hand.

## Commands

```bash
python3 scripts/generate-index.py            # regenerate catalog/index.json (run after ANY change to skills/manifests)
python3 scripts/generate-index.py --check    # fails if the index is stale OR any SKILL.md frontmatter is malformed
claude plugin validate .                     # validate marketplace + every local plugin (--strict = warnings become errors)
claude plugin validate ./plugins/<name>      # validate a single plugin
python3 plugins/plaud/scripts/tests/test_engine.py   # offline test for the plaud sync engine (exit 0 = pass)
python3 plugins/sdd/scripts/tests/test_sdd_scripts.py  # offline test for the sdd state scripts (exit 0 = pass)
```

To try a plugin locally: `claude plugin marketplace add ./` then `claude plugin install <name>@bruno-skills`, and `/reload-plugins` in the session. Everything is stdlib Python 3.7+; there are no package installs, linters, or build steps.

## Single source of truth

Each metadata field has one canonical home; the index generator reads them in this priority and the copies must not drift:

| Field | Canonical source |
|-------|------------------|
| `description` | `SKILL.md` frontmatter (3rd person, what it does + when to use, trigger keywords) |
| `version`, `author`, `license` | plugin's `plugin.json` |
| `category`, `keywords` | plugin's entry in `.claude-plugin/marketplace.json` |

The `description` is intentionally duplicated in `SKILL.md`, `plugin.json`, and the marketplace entry — keep all three **identical**, with `SKILL.md` as canonical. `category` must be one of the values in `docs/categories.json`.

## Frontmatter constraints (hard errors)

`scripts/generate-index.py` uses a hand-rolled YAML parser, so `SKILL.md` frontmatter must stay within its subset — anything else fails the build loudly:

- one `key: value` per line; block scalars (`>`/`|`) allowed for long values, indented with **spaces, not tabs**
- no sequences (`- item`); no inline `# comments` on plain scalars
- only `metadata:` may hold a nested map (string→string)
- `name` must equal the skill's directory name; Agent Skills rules apply (≤64 chars, lowercase/digits/hyphens, no `--`, must not contain `claude`/`anthropic`)

## Adding a skill

Follow the 6-step workflow in README.md ("Add a new skill"): create `plugins/<name>/.claude-plugin/plugin.json` → write `skills/<name>/SKILL.md` → pick a category from `docs/categories.md` → register the plugin in `marketplace.json` → regenerate the index → validate. Commit the plugin folder, `marketplace.json`, and the regenerated `catalog/index.json` together.

Skill bodies stay under 500 lines; depth goes into `references/`, code into `scripts/`, static files into `assets/`.

## Plugin-specific invariants

- **plaud**: bundles the Plaud MCP server via `.mcp.json`. The sync engine (`plugins/plaud/scripts/plaud_sync.py`) has a security invariant enforced by its test: **signed URLs (`X-Amz-*`) are never persisted** — only the Plaud `id` is stored in notes and the checkpoint. Keep the engine drivable as a subprocess (that is how the skills call it and how the test runs it).
- **sdd**: 6 skills (pt-BR by design) whose cycle state lives in files, never in the conversation: `docs/sdd/` (spec, sprint plan with a `Status:` line per sprint file, `status.md` panel) and `TECH_DEBT.md`. Those files are maintained **only** through the deterministic scripts (`scripts/tech_debt.py`, `scripts/sdd_status.py`) — keep them drivable as subprocesses (that is how the skills call them and how the test runs them). The gates (`verify-sprint`, `review-quality`) run as forks inside the edit-less agent containers in `agents/` (no Write/Edit); `run-sprints` delegates each sprint to the `sprint-executor` agent by **file path**, never pasted content.
- **skill-lab**: single-skill plugin (`harden-skill`); its description must stay identical across SKILL.md, plugin.json and the marketplace entry (the generator enforces it).

## Conventions

Commit messages follow Conventional Commits with pt-BR summaries (e.g. `feat(plaud): …`, `harden(sdd): …`, `docs: …`).
