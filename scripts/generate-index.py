#!/usr/bin/env python3
"""Generate catalog/index.json for the bruno-skills marketplace.

Reads the marketplace manifest, each plugin manifest, and each skill's SKILL.md
frontmatter, then emits a machine-readable catalog index. Pure Python standard
library — no external dependencies (a hand-rolled frontmatter parser stands in
for PyYAML so the script runs anywhere python3 >= 3.7 does).

Canonical sources (do not guess — read them):
  - description : SKILL.md frontmatter (the skill's own truth)
  - version     : plugin.json  (authoritative; falls back to SKILL.md metadata)
  - author      : plugin.json  (falls back to SKILL.md metadata)
  - license     : plugin.json  (falls back to SKILL.md frontmatter)
  - category    : the plugin's marketplace entry (a marketplace-only field)
  - keywords    : the plugin's marketplace entry (falls back to plugin.json)
  - homepage/repository : plugin.json (optional)

Accepted SKILL.md frontmatter (kept deliberately small — the parser rejects,
loudly, anything it cannot model rather than mangling it silently):
  - one `key: scalar` per line; no YAML block scalars (`>`, `|`); no sequences
    (`- item`); no inline `# comments`; only `metadata:` may hold a nested map.
Anything outside this is a hard error, so a stale OR malformed index both fail.

Category values are validated against docs/categories.json (the canonical
taxonomy). `name` must match the skill's directory (Agent Skills rule).

Usage:
    python3 scripts/generate-index.py            # write catalog/index.json
    python3 scripts/generate-index.py --check     # exit 1 if stale or malformed
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"
CATEGORIES = REPO / "docs" / "categories.json"
OUT = REPO / "catalog" / "index.json"
GENERATOR = {"script": "scripts/generate-index.py", "version": "1.1"}

_BLOCK_SCALAR = re.compile(r"^[>|][+-]?\d*$")  # >, |, >-, |+, |2, ...


def rel(path: Path) -> str:
    """Repo-relative path for messages, defensively (never raises)."""
    try:
        return str(Path(path).resolve().relative_to(REPO))
    except Exception:
        return str(path)


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.stderr.write(f"generate-index: error: {msg}\n")
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.is_file():
        die(f"missing required file: {rel(path)}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {rel(path)}: {exc}")
    if not isinstance(data, dict):
        die(f"expected a JSON object in {rel(path)}, got {type(data).__name__}")
    return data


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str, path: Path) -> dict:
    """Parse the small YAML subset SKILL.md frontmatter is allowed to use.

    Supports top-level `key: scalar` and a single nested `metadata:` map of
    `  key: scalar` pairs. Rejects (hard error) block scalars, sequences, and
    stray indentation — so an author who writes an unsupported construct gets a
    clear failure instead of a silently wrong index.
    """
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        die(f"no YAML frontmatter found in {rel(path)}")
    data: dict = {}
    current_key = None  # the top-level mapping key we're nested under
    for lineno, raw in enumerate(m.group(1).splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        stripped = raw.strip()
        if stripped == "-" or stripped.startswith("- "):
            die(f"{rel(path)}:{lineno}: YAML sequences are not supported in frontmatter")
        if raw[0] in " \t":  # nested line
            if current_key is None or not isinstance(data.get(current_key), dict):
                die(
                    f"{rel(path)}:{lineno}: unexpected indented line — only 'metadata:' "
                    f"may hold a nested map, and multi-line values are not supported: {raw!r}"
                )
            key, sep, val = stripped.partition(":")
            if not sep:
                die(f"{rel(path)}:{lineno}: malformed frontmatter line: {raw!r}")
            data[current_key][key.strip()] = _strip_quotes(val.strip())
            continue
        key, sep, val = raw.partition(":")
        if not sep:
            die(f"{rel(path)}:{lineno}: malformed frontmatter line: {raw!r}")
        key, val = key.strip(), val.strip()
        if val == "":
            data[key] = {}
            current_key = key
        elif _BLOCK_SCALAR.match(val):
            die(
                f"{rel(path)}:{lineno}: block scalars ('{val}') are not supported; "
                f"keep '{key}' on a single line"
            )
        else:
            data[key] = _strip_quotes(val)
            current_key = None
    return data


def require_str(value: object, what: str, path: Path) -> str:
    if not isinstance(value, str) or not value.strip():
        die(f"{rel(path)}: '{what}' must be a non-empty single-line string")
    return value


def normalize_author(author: object, path: Path) -> dict:
    """Coerce an author (dict or bare-name string) into a stable {name, email?}."""
    if isinstance(author, dict):
        name = author.get("name")
        if not name:
            die(f"{rel(path)}: author is missing a name")
        out = {"name": name}
        if author.get("email"):
            out["email"] = author["email"]
        return out
    if isinstance(author, str) and author.strip():
        return {"name": author}
    die(f"{rel(path)}: author is required (a name string or a {{name, email}} object)")


def valid_categories() -> set:
    cats = load_json(CATEGORIES).get("categories", [])
    slugs = {c["slug"] for c in cats if isinstance(c, dict) and "slug" in c}
    if not slugs:
        die("docs/categories.json has no category slugs")
    return slugs


def build_index() -> dict:
    marketplace = load_json(MARKETPLACE)
    allowed = valid_categories()
    skills: list = []

    for entry in marketplace.get("plugins", []):
        plugin_name = entry.get("name")
        source = entry.get("source", "")
        if not plugin_name or not source:
            die(f"marketplace entry missing name/source: {entry!r}")

        plugin_dir = (REPO / source).resolve()
        try:  # reject sources that escape the repo (path traversal)
            plugin_dir.relative_to(REPO)
        except ValueError:
            die(f"plugin '{plugin_name}': source '{source}' escapes the repository")

        plugin_json_path = plugin_dir / ".claude-plugin" / "plugin.json"
        plugin_json = load_json(plugin_json_path)

        category = entry.get("category")
        if category is None:
            die(f"plugin '{plugin_name}' has no category in its marketplace entry")
        if category not in allowed:
            die(
                f"plugin '{plugin_name}': category '{category}' is not in "
                f"docs/categories.json (allowed: {', '.join(sorted(allowed))})"
            )

        version = plugin_json.get("version")
        author = plugin_json.get("author")
        license_ = plugin_json.get("license")

        skill_files = sorted((plugin_dir / "skills").glob("*/SKILL.md"))
        if not skill_files:
            die(f"plugin '{plugin_name}' has no skills/*/SKILL.md")

        for skill_md in skill_files:
            skill_dir = skill_md.parent.name
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"), skill_md)
            meta = fm.get("metadata") if isinstance(fm.get("metadata"), dict) else {}

            name = fm.get("name", skill_dir)
            name = require_str(name, "name", skill_md)
            if name != skill_dir:  # Agent Skills rule: name matches the directory
                die(f"{rel(skill_md)}: name '{name}' must match its directory '{skill_dir}'")

            eff_version = version if version is not None else meta.get("version")
            if eff_version is None:
                die(f"skill '{name}': no version in plugin.json or SKILL.md metadata")

            record = {
                "id": f"{plugin_name}/{skill_dir}",
                "name": name,
                "plugin": plugin_name,
                "description": require_str(fm.get("description"), "description", skill_md),
                "category": category,
                "keywords": entry.get("keywords", plugin_json.get("keywords", [])),
                "author": normalize_author(author if author is not None else meta.get("author"), skill_md),
                "version": require_str(str(eff_version), "version", skill_md),
                "license": require_str(license_ if license_ is not None else fm.get("license"), "license", skill_md),
                "source": source,
                "path": f"{source.rstrip('/')}/skills/{skill_dir}/SKILL.md",
            }
            for opt in ("homepage", "repository"):
                if plugin_json.get(opt):
                    record[opt] = plugin_json[opt]
            skills.append(record)

    skills.sort(key=lambda r: r["id"])
    return {
        "marketplace": {
            "name": marketplace.get("name"),
            "owner": marketplace.get("owner"),
            "description": marketplace.get("description"),
        },
        "generator": GENERATOR,
        "skills": skills,
    }


def render(index: dict) -> str:
    return json.dumps(index, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv: list) -> int:
    rendered = render(build_index())
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if current != rendered:
            die("catalog/index.json is stale — run: python3 scripts/generate-index.py")
        print("catalog/index.json is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {rel(OUT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
