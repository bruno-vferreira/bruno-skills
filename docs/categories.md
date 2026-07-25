# Category Taxonomy

This is the controlled vocabulary of categories for the `bruno-skills` marketplace.
Every skill in the catalog is assigned **exactly one** `category` from this list, and
each value must match a slug verbatim (lowercase, kebab-case).

> **Canonical source:** [`categories.json`](./categories.json) is the machine-readable
> source of truth. The catalog index generator reads the valid slugs from that file and
> validates each skill's `category` against it. **This Markdown file is a human-readable
> projection** — the table below mirrors `categories.json`; edit the JSON, not the table.

| Category | Description |
|----------|-------------|
| `documents` | Creating, parsing, or transforming document formats (PDF, DOCX, XLSX, PPTX, and similar). |
| `creative-design` | Visual, artistic, or design output — image generation, layout, branding, and art. |
| `development` | Software development support: coding, git workflows, refactoring, and build tooling. |
| `data` | Data manipulation, analysis, transformation, querying, and pipelines. |
| `testing` | Writing, running, or reasoning about tests and test coverage. |
| `devops` | Infrastructure, deployment, CI/CD, containers, and operations. |
| `security` | Security review, auditing, secrets handling, and hardening. |
| `productivity` | Streamlining everyday personal and team workflows. |
| `communication` | Writing, messaging, internal comms, and correspondence. |
| `marketing` | Marketing content, copywriting, campaigns, and growth. |
| `meta` | Skills about skills: authoring, evaluating, or managing other skills. |

## Rules

- A skill's `category` value **must** be one of the slugs above, spelled exactly.
- **Where `category` lives:** it is declared on the plugin's entry in
  `.claude-plugin/marketplace.json` (it is a marketplace-only field, not a `plugin.json`
  field). Because this marketplace maps one plugin to one skill, category-per-plugin is
  category-per-skill; the catalog index reads it from the marketplace entry.
- Use `keywords` (free-form) for finer granularity beyond the single category. `keywords`
  is the standard manifest field and is the single source of discovery terms — set it on
  the plugin's marketplace entry (and, if present, keep `plugin.json` `keywords` identical).
- Adding a new category is a deliberate change: update [`categories.json`](./categories.json)
  first (the canonical source), then regenerate this projection and update the affected
  skill metadata and the generated catalog index.
