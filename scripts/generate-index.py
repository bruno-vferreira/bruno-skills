#!/usr/bin/env python3
"""Generate catalog/index.json for the bruno-skills marketplace.

Reads the marketplace manifest, each plugin manifest, and each skill's SKILL.md
frontmatter, then emits a machine-readable catalog index. Pure Python standard
library — no external dependencies (a hand-rolled frontmatter parser stands in
for PyYAML so the script runs anywhere python3 does).

Canonical sources (do not guess — read them):
  - description : SKILL.md frontmatter (the skill's own truth)
  - version     : plugin.json  (authoritative; falls back to SKILL.md metadata)
  - author      : plugin.json  (falls back to SKILL.md metadata)
  - license     : plugin.json  (falls back to SKILL.md frontmatter)
  - category    : the plugin's marketplace entry (a marketplace-only field)
  - keywords    : the plugin's marketplace entry (falls back to plugin.json)
  - homepage/repository : plugin.json (optional)

Category values are validated against docs/categories.json (the canonical
taxonomy). An unknown category is a hard error.

Usage:
    python3 scripts/generate-index.py            # write catalog/index.json
    python3 scripts/generate-index.py --check     # exit 1 if the file is stale
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
GENERATOR = {"script": "scripts/generate-index.py", "version": "1.0"}


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.stderr.write(f"generate-index: error: {msg}\n")
    raise SystemExit(1)


def load_json(path: Path) -> dict:
    if not path.is_file():
        die(f"missing required file: {path.relative_to(REPO)}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"invalid JSON in {path.relative_to(REPO)}: {exc}")


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_frontmatter(text: str, path: Path) -> dict:
    """Minimal YAML-frontmatter parser for the fields SKILL.md uses.

    Handles top-level `key: value` scalars and a single nested `metadata:` map
    of `  key: value` pairs. Sufficient for the Agent Skills frontmatter schema;
    not a general YAML parser.
    """
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        die(f"no YAML frontmatter found in {path.relative_to(REPO)}")
    data: dict = {}
    current_map = None
    for raw in m.group(1).splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if re.match(r"^\S", raw):  # top-level key
            key, _, val = raw.partition(":")
            key, val = key.strip(), val.strip()
            if val == "":
                data[key] = {}
                current_map = data[key]
            else:
                data[key] = _strip_quotes(val)
                current_map = None
        elif current_map is not None:  # nested under the last mapping key
            key, _, val = raw.strip().partition(":")
            current_map[key.strip()] = _strip_quotes(val.strip())
    return data


def valid_categories() -> set[str]:
    cats = load_json(CATEGORIES).get("categories", [])
    slugs = {c["slug"] for c in cats if "slug" in c}
    if not slugs:
        die("docs/categories.json has no category slugs")
    return slugs


def build_index() -> dict:
    marketplace = load_json(MARKETPLACE)
    allowed = valid_categories()
    skills: list[dict] = []

    for entry in marketplace.get("plugins", []):
        plugin_name = entry.get("name")
        source = entry.get("source", "")
        if not plugin_name or not source:
            die(f"marketplace entry missing name/source: {entry!r}")
        plugin_dir = (REPO / source).resolve()
        plugin_json = load_json(plugin_dir / ".claude-plugin" / "plugin.json")

        category = entry.get("category")
        if category is None:
            die(f"plugin '{plugin_name}' has no category in its marketplace entry")
        if category not in allowed:
            die(
                f"plugin '{plugin_name}': category '{category}' is not in "
                f"docs/categories.json (allowed: {', '.join(sorted(allowed))})"
            )

        skill_files = sorted((plugin_dir / "skills").glob("*/SKILL.md"))
        if not skill_files:
            die(f"plugin '{plugin_name}' has no skills/*/SKILL.md")

        for skill_md in skill_files:
            fm = parse_frontmatter(skill_md.read_text(encoding="utf-8"), skill_md)
            meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
            record = {
                "name": fm.get("name") or skill_md.parent.name,
                "plugin": plugin_name,
                "description": fm.get("description", ""),
                "category": category,
                "keywords": entry.get("keywords", plugin_json.get("keywords", [])),
                "author": plugin_json.get("author", meta.get("author")),
                "version": plugin_json.get("version", meta.get("version")),
                "license": plugin_json.get("license", fm.get("license")),
                "source": source,
            }
            # Optional fields only when present.
            for opt in ("homepage", "repository"):
                if plugin_json.get(opt):
                    record[opt] = plugin_json[opt]
            skills.append(record)

    skills.sort(key=lambda r: (r["plugin"], r["name"]))
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


def main(argv: list[str]) -> int:
    index = build_index()
    rendered = render(index)
    if "--check" in argv:
        current = OUT.read_text(encoding="utf-8") if OUT.is_file() else ""
        if current != rendered:
            die("catalog/index.json is stale — run: python3 scripts/generate-index.py")
        print("catalog/index.json is up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(rendered, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)} ({len(index['skills'])} skill(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
