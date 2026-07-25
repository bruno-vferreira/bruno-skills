---
name: commit-message
description: Generates a Conventional Commits message by analyzing the staged git diff (git diff --cached). Use when the user asks for help writing a commit message, wants to commit staged changes, or mentions commit messages, staged diffs, or conventional commits.
license: MIT
metadata:
  author: Bruno Ferreira
  version: "0.1.0"
---

# Commit Message

Write a clear, correct [Conventional Commits](https://www.conventionalcommits.org)
message for changes that are already **staged** in git.

## When to use

Use this when the user wants help writing a commit message, is about to commit staged
changes, or mentions commit messages, staged diffs, or conventional commits.

## Procedure

### 1. Read the staged changes

Inspect only what is **staged** — the message must describe what will actually be
committed, not unstaged edits:

```bash
git diff --cached --stat   # files touched + churn, for scope
git diff --cached          # the actual change, to understand intent
```

If `git diff --cached` is empty, **stop** and tell the user nothing is staged (offer
`git add`). Never invent a message for changes you cannot see.

### 2. Decide the type

Pick the single type that best fits the primary intent of the change:

| Type | Use for |
|------|---------|
| `feat` | A new feature or capability |
| `fix` | A bug fix |
| `docs` | Documentation only |
| `style` | Formatting/whitespace; no code-behavior change |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | A change that improves performance |
| `test` | Adding or correcting tests |
| `build` | Build system or external dependencies |
| `ci` | CI configuration and scripts |
| `chore` | Maintenance that doesn't touch src or tests |
| `revert` | Reverts a previous commit |

If the diff mixes concerns (e.g. a fix **and** an unrelated feature), say so and suggest
splitting into separate commits rather than forcing one type.

### 3. Decide the scope (optional)

A short noun for the affected area, in parentheses — usually a module, package, or
directory (`api`, `auth`, `parser`). Omit it if the change is broad or no single scope
fits. Keep it lowercase.

### 4. Write the subject line

Format: `type(scope): description`

- **Imperative mood** — "add", not "added"/"adds".
- **Lowercase** description, **no trailing period**.
- Keep the whole subject **≤ 72 characters** (50 is a good target).
- Describe *what changes and why it matters*, not the mechanics of the diff.

### 5. Add a body and footer when they earn their place

- **Body** (optional): wrap at ~72 columns; explain the *what* and *why*, not the *how*.
  Add it when the subject alone can't carry the reasoning.
- **Breaking changes**: add a footer line `BREAKING CHANGE: <what broke and the migration>`
  (and/or a `!` after the type/scope: `feat(api)!: ...`).
- **Issue references**: footer such as `Refs: #123` or `Closes: #123`.

### 6. Output

Present the final message in a single fenced code block so the user can copy it, for
example:

```text
git commit -m "feat(parser): support quoted CSV fields with embedded commas"
```

For a multi-line message, show the full subject + body + footer inside the block. Do not
run the commit unless the user asks.

## Examples

Simple:

```text
fix(auth): reject expired refresh tokens
```

With body and footer:

```text
refactor(index): stream large catalogs instead of loading them fully

Building the catalog held every entry in memory before writing, which spiked
memory on large repos. Stream entries to the writer so peak memory stays flat.

Refs: #142
```

Breaking change:

```text
feat(config)!: rename `apiKey` to `token`

BREAKING CHANGE: the `apiKey` field is removed. Rename it to `token` in config files.
```

## Rules of thumb

- One logical change per commit; suggest splitting when the diff says otherwise.
- The subject answers "if applied, this commit will…" — it must complete that sentence.
- Prefer clarity over cleverness; a future reader with no context should understand it.
