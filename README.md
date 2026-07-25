# bruno-skills

A personal, standards-faithful **marketplace of Agent Skills** for Claude Code.

Every skill here follows the open [Agent Skills](https://agentskills.io) standard
(the `SKILL.md` format) and the repository is a valid [Claude Code plugin
marketplace](https://code.claude.com/docs/en/plugin-marketplaces), so any skill in it
can be installed with a single command. A machine-readable catalog lives at
[`catalog/index.json`](./catalog/index.json), generated from the repo — the basis for a
browsable site later.

## What's inside

```text
.
├── .claude-plugin/
│   └── marketplace.json        # the marketplace manifest (lists every plugin)
├── plugins/                    # one folder per plugin; a plugin bundles 1+ skills
│   ├── commit-message/
│   │   ├── .claude-plugin/
│   │   │   └── plugin.json      # plugin manifest (version, author, license, keywords)
│   │   └── skills/
│   │       └── commit-message/
│   │           └── SKILL.md     # the skill itself (Agent Skills format)
│   └── sdd/                     # a multi-skill plugin (8 spec-driven-development skills)
│       ├── .claude-plugin/
│       │   └── plugin.json
│       └── skills/
│           └── <spec, decompose, execute-sprint, verify-sprint, review,
│               review-and-fix, build-project, harden-skill>/SKILL.md (+ assets/)
├── catalog/
│   └── index.json              # generated catalog index (do not edit by hand)
├── docs/
│   ├── categories.json         # canonical category taxonomy (machine-readable)
│   └── categories.md           # human-readable projection of the taxonomy
├── scripts/
│   └── generate-index.py       # regenerates catalog/index.json (Python 3.7+, stdlib only)
└── LICENSE                     # MIT
```

**Where each field lives (single source of truth):**

| Field | Canonical source |
|-------|------------------|
| `description` | the skill's `SKILL.md` frontmatter (3rd person, what it does + when to use it) |
| `version`, `author`, `license` | the plugin's `plugin.json` |
| `category`, `keywords` | the plugin's entry in `marketplace.json` |
| `homepage`, `repository` | the plugin's `plugin.json` (optional) |

Some fields (e.g. `author`, `version`) also appear in `SKILL.md`'s `metadata` so the
skill is valid on its own under the Agent Skills standard. Those copies are a fallback —
the canonical source in the table always wins in the generated index.

The catalog currently holds two plugins:

- **`commit-message`** — a single skill that writes a
  [Conventional Commits](https://www.conventionalcommits.org) message from the staged git diff.
- **`sdd`** — Spec-Driven Development: an 8-skill methodology (spec → decompose → execute →
  verify → review), the `build-project` and `review-and-fix` orchestrators, and the
  `harden-skill` eval builder. Once installed, its commands are namespaced as
  `/sdd:<skill>` (e.g. `/sdd:build-project`); the skills also trigger from natural language.

## Install

From this repository, hosted on GitHub:

```bash
claude plugin marketplace add bruno-vferreira/bruno-skills # add the marketplace
claude plugin install commit-message@bruno-skills          # install a skill
```

Or from a local clone (useful while developing):

```bash
claude plugin marketplace add ./
claude plugin install commit-message@bruno-skills
```

Then activate it in the current session:

```text
/reload-plugins
```

> Relative-path plugin sources resolve only when the whole repo is cloned (i.e.
> git-hosted), which is why the marketplace is added by GitHub `owner/repo` or a local
> path, not by a bare URL to `marketplace.json`.

Add `--scope local` to any `marketplace add` / `plugin install` command to keep the
change to this project's gitignored local settings instead of your user settings.

## Add a new skill

Say you're adding a skill called `my-skill`.

1. **Create the plugin folder and manifest** at `plugins/my-skill/.claude-plugin/plugin.json`:

   ```json
   {
     "name": "my-skill",
     "description": "Does X. Use when the user mentions X, Y, or Z.",
     "version": "0.1.0",
     "author": { "name": "Bruno Ferreira", "email": "bvferreira@hotmail.com" },
     "license": "MIT",
     "keywords": ["keyword-one", "keyword-two"]
   }
   ```

2. **Write the skill** at `plugins/my-skill/skills/my-skill/SKILL.md`. The folder name
   **must** equal the `name` in the frontmatter:

   ```markdown
   ---
   name: my-skill
   description: Does X. Use when the user mentions X, Y, or Z.
   license: MIT
   metadata:
     author: Bruno Ferreira
     version: "0.1.0"
   ---

   # My Skill

   Instructions for the model go here.
   ```

   Frontmatter rules (Agent Skills standard):
   - `name` — 1–64 chars, lowercase letters/digits/hyphens, no leading/trailing hyphen,
     no `--`, and **equal to the skill's directory name**. Must not contain `claude` or
     `anthropic`, or XML tags.
   - `description` — ≤1024 chars, **third person**, saying **what it does and when to use
     it**, with concrete trigger keywords. This is what Claude matches on.
   - `license` — e.g. `MIT`; `metadata` — a string→string map (put `author`/`version` here).
   - Keep the body under 500 lines; move depth into `references/`, code into `scripts/`,
     assets into `assets/`.

3. **Pick a category** from the taxonomy in [`docs/categories.md`](./docs/categories.md)
   (canonical list: [`docs/categories.json`](./docs/categories.json)).

4. **Register the plugin** in `.claude-plugin/marketplace.json` by adding an entry to
   `plugins` (`category` and `keywords` are declared here):

   ```json
   {
     "name": "my-skill",
     "source": "./plugins/my-skill",
     "description": "Does X. Use when the user mentions X, Y, or Z.",
     "category": "development",
     "keywords": ["keyword-one", "keyword-two"]
   }
   ```

   Keep the `description` identical across `SKILL.md`, `plugin.json`, and this entry;
   the `SKILL.md` text is canonical. Leave `version`/`author`/`license` out of this entry
   — they come from `plugin.json`.

5. **Regenerate the catalog index:**

   ```bash
   python3 scripts/generate-index.py
   ```

6. **Validate** (see below), then commit `plugins/my-skill/`, the updated
   `marketplace.json`, and the regenerated `catalog/index.json`.

## Validate

```bash
claude plugin validate .                          # marketplace + every local plugin
claude plugin validate ./plugins/commit-message   # a single plugin (add --strict to fail on warnings)
python3 scripts/generate-index.py --check         # index is fresh AND frontmatter is well-formed
```

- `claude plugin validate` checks the `marketplace.json` / `plugin.json` schemas and skill
  frontmatter. `--strict` turns warnings into errors.
- `python3 scripts/generate-index.py --check` exits non-zero if `catalog/index.json` is
  stale **or** if any `SKILL.md` frontmatter is malformed — regenerate to fix.
- Optionally, the open-standard validator: `skills-ref validate ./plugins/<plugin>/skills/<skill>`
  (from [agentskills/agentskills](https://github.com/agentskills/agentskills); it may not
  be installed).

### Frontmatter the index generator accepts

The generator ships a small hand-rolled parser (no external dependencies), so `SKILL.md`
frontmatter must stay within a small YAML subset — anything else is a **hard error**
(never a silently wrong index):

- one `key: value` per line; YAML block scalars (`>`/`|`, folded or literal) are
  supported for long values (indent the body with **spaces, not tabs**);
- no sequences (`- item`);
- no inline `# comments` on plain scalars (a `#` inside a block scalar is literal text);
- only `metadata:` may hold a nested map.

Requires **Python 3.7+**. No third-party packages.

## License

[MIT](./LICENSE) © Bruno Ferreira
