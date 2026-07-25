# Category Taxonomy

This is the controlled vocabulary of categories for the `bruno-skills` marketplace.
Every skill in the catalog is assigned **exactly one** `category` from this list. The
catalog index generator and the marketplace metadata both draw from these slugs, so
they must match verbatim (lowercase, kebab-case).

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
- Use `tags` (free-form) for finer granularity beyond the single category.
- Adding a new category is a deliberate change: update this file first, then the
  affected skill metadata and the generated catalog index.
