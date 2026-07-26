#!/usr/bin/env python3
"""Deterministic engine for the `plaud` plugin's sync skills.

The Plaud MCP tools (`list_files`, `get_file`) belong to Claude, not to a CLI —
so this engine never calls the MCP. The skill calls the MCP and pipes the JSON
here; this script does the deterministic disk-side work that a model should not
improvise per run: diffing server vs. local, parsing the nested JSON, writing
`nota.md`, downloading the audio, and updating the checkpoint.

Subcommands (all take `--root <dir>`, the project dir where `.plaud/` lives):

  diff      stdin = `list_files` JSON  -> stdout: which recordings need syncing
            (id absent from the checkpoint OR local nota.md/audio.mp3 missing).
  save      stdin = `get_file` JSON    -> writes recordings/<date>-<slug>/nota.md,
            downloads audio.mp3 (skips if a non-empty file already exists), and
            upserts that recording's checkpoint record. Prints a status line.
  finalize  updates the checkpoint's top-level fields (version, last_synced_at,
            last_created_at watermark, user). `--rebuild` also prunes records
            whose folder no longer exists on disk (used by sync-all).

Security invariant: the presigned audio URL and any signed `data_link` carry a
temporary AWS token and expire — they are NEVER written to nota.md or the
checkpoint. Only the stable Plaud `id` is persisted. `get_file` is called fresh
each run, so the 24h audio URL never goes stale mid-run.

Pure Python standard library — runs anywhere python3 >= 3.8 does.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

CHECKPOINT_VERSION = 1
RECORDINGS_SUBDIR = "recordings"
NOTE_NAME = "nota.md"
AUDIO_NAME = "audio.mp3"
SLUG_MAXLEN = 60
DOWNLOAD_TIMEOUT = 300  # seconds; audio of long meetings can be tens of MB


# --------------------------------------------------------------------------- #
# small helpers
# --------------------------------------------------------------------------- #
def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def plaud_dir(root: Path) -> Path:
    return root / ".plaud"


def checkpoint_path(root: Path) -> Path:
    return plaud_dir(root) / "checkpoint.json"


def load_checkpoint(root: Path) -> dict:
    path = checkpoint_path(root)
    if not path.is_file():
        return {"version": CHECKPOINT_VERSION, "recordings": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # A corrupt checkpoint should not wedge a sync — treat as empty and let
        # this run rebuild it. (sync/sync-all both rewrite it at the end.)
        return {"version": CHECKPOINT_VERSION, "recordings": {}}
    if not isinstance(data, dict):
        return {"version": CHECKPOINT_VERSION, "recordings": {}}
    data.setdefault("recordings", {})
    if not isinstance(data["recordings"], dict):
        data["recordings"] = {}
    return data


def write_checkpoint(root: Path, data: dict) -> None:
    path = checkpoint_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_stdin_json() -> object:
    raw = sys.stdin.read()
    if not raw.strip():
        die("expected JSON on stdin, got nothing")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        die(f"invalid JSON on stdin: {exc}")


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.stderr.write(f"plaud_sync: error: {msg}\n")
    raise SystemExit(1)


# --------------------------------------------------------------------------- #
# formatting: slug, dates, timestamps, YAML scalars
# --------------------------------------------------------------------------- #
def slugify(name: str) -> str:
    """ASCII, lowercase, hyphen-separated slug, truncated at a word boundary."""
    if not name:
        return "sem-titulo"
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_only = nfkd.encode("ascii", "ignore").decode("ascii")
    ascii_only = ascii_only.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_only).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    if len(slug) > SLUG_MAXLEN:
        cut = slug[:SLUG_MAXLEN]
        # avoid slicing mid-word when there's a nearby hyphen to cut at
        if "-" in cut:
            cut = cut[: cut.rfind("-")]
        slug = cut.strip("-")
    return slug or "sem-titulo"


def date_prefix(rec: dict) -> str:
    """YYYY-MM-DD from start_at, falling back to created_at, then 'sem-data'."""
    for key in ("start_at", "created_at"):
        val = rec.get(key)
        if isinstance(val, str) and len(val) >= 10 and val[4] == "-" and val[7] == "-":
            return val[:10]
    return "sem-data"


def folder_for(rec: dict, rec_id: str, taken: dict) -> str:
    """Relative folder (under .plaud/) for a recording.

    `taken` maps folder -> id for folders already assigned. On a collision with
    a *different* id, append a short id suffix so two same-day same-name
    recordings never share a directory. A folder already owned by this id is
    reused verbatim (stable across runs).
    """
    base = f"{date_prefix(rec)}-{slugify(rec.get('name', ''))}"
    candidate = f"{RECORDINGS_SUBDIR}/{base}"
    owner = taken.get(candidate)
    if owner is None or owner == rec_id:
        return candidate
    return f"{RECORDINGS_SUBDIR}/{base}-{rec_id[:8]}"


def to_ms(value: object) -> int:
    """Coerce a duration to int milliseconds — handles int, float, and numeric
    strings ('1179000', '1179000.0'); returns 0 when uncoercible."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def hms(ms: object) -> str:
    """Milliseconds -> M:SS or H:MM:SS timestamp label."""
    total = to_ms(ms) // 1000
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def human_duration(ms: object) -> str:
    """Milliseconds -> compact human duration like '19m39s' or '1h05m03s'.
    Empty string for a missing/zero/uncoercible duration."""
    total = to_ms(ms) // 1000
    if total <= 0:
        return ""
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h{m:02d}m{s:02d}s"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def yamlq(value: object) -> str:
    """Emit a safe single-line YAML scalar (double-quoted when needed)."""
    if value is None:
        return '""'
    s = str(value)
    if s == "":
        return '""'
    reserved = {"true", "false", "null", "yes", "no", "on", "off", "~"}
    looks_numeric = bool(re.fullmatch(r"[+-]?\d+(\.\d+)?([eE][+-]?\d+)?", s))
    if (
        s == s.strip()
        and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._/-]*", s)
        and s.lower() not in reserved
        and not looks_numeric  # keep numeric-looking strings (serial_number) as strings
    ):
        return s  # plain, unambiguous scalar: safe unquoted
    escaped = (
        s.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'


# --------------------------------------------------------------------------- #
# parsing the get_file payload
# --------------------------------------------------------------------------- #
def _parse_inner(content: object) -> list:
    """A `data_content` is a JSON-encoded string; parse it into a list."""
    if isinstance(content, list):
        return content
    if isinstance(content, str) and content.strip():
        try:
            parsed = json.loads(content)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []
    return []


def extract_sections(payload: dict) -> dict:
    """Pull transcript segments, outline topics, and the summary note text."""
    transcript: list = []
    outline: list = []
    for src in payload.get("source_list") or []:
        if not isinstance(src, dict):
            continue
        dtype = src.get("data_type")
        if dtype == "transaction":
            transcript = _parse_inner(src.get("data_content"))
        elif dtype == "outline":
            outline = _parse_inner(src.get("data_content"))
    summary = ""
    for note in payload.get("note_list") or []:
        if not isinstance(note, dict):
            continue
        if note.get("data_type") == "auto_sum_note" or not summary:
            content = note.get("data_content")
            if isinstance(content, str) and content.strip():
                summary = content
                if note.get("data_type") == "auto_sum_note":
                    break
    return {"transcript": transcript, "outline": outline, "summary": summary}


def _demote_headings(md: str) -> str:
    """Demote markdown headings one level so the note nests under `## Resumo`
    (keeps a single H1 — the recording name — in the document)."""
    out = []
    for line in md.splitlines():
        m = re.match(r"^(#{1,5})(\s)", line)
        if m:
            line = "#" + line
        out.append(line)
    return "\n".join(out)


def render_note(payload: dict, sections: dict, audio_present: bool) -> str:
    name = payload.get("name") or "(sem título)"
    title = " ".join(str(name).split())  # single-line heading (collapse any newlines)
    audio_field = yamlq(AUDIO_NAME) if audio_present else '""'
    fm = [
        "---",
        f"id: {yamlq(payload.get('id'))}",
        f"name: {yamlq(name)}",
        f"date: {yamlq(date_prefix(payload))}",
        f"start_at: {yamlq(payload.get('start_at'))}",
        f"created_at: {yamlq(payload.get('created_at'))}",
        f"duration_ms: {to_ms(payload.get('duration'))}",
        f"duration: {yamlq(human_duration(payload.get('duration')))}",
        f"serial_number: {yamlq(payload.get('serial_number'))}",
        f"audio: {audio_field}",
        "source: plaud",
        f"synced_at: {yamlq(now_iso())}",
        "---",
        "",
        f"# {title}",
        "",
    ]

    body = ["## Resumo", ""]
    if sections["summary"]:
        body.append(_demote_headings(sections["summary"]).strip())
    else:
        body.append("_Sem nota-resumo disponível._")
    body.append("")

    body.append("## Tópicos")
    body.append("")
    if sections["outline"]:
        for topic in sections["outline"]:
            if isinstance(topic, dict) and topic.get("topic"):
                body.append(f"- [{hms(topic.get('start_time'))}] {topic['topic']}")
    else:
        body.append("_Sem tópicos disponíveis._")
    body.append("")

    body.append("## Transcrição")
    body.append("")
    if sections["transcript"]:
        for seg in sections["transcript"]:
            if not isinstance(seg, dict):
                continue
            speaker = seg.get("speaker") or seg.get("original_speaker") or "?"
            content = (seg.get("content") or "").strip()
            if not content:
                continue
            body.append(f"**{speaker}** [{hms(seg.get('start_time'))}]")
            body.append("")
            body.append(content)
            body.append("")
    else:
        body.append("_Sem transcrição disponível._")
        body.append("")

    return "\n".join(fm + body).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# audio download
# --------------------------------------------------------------------------- #
def download_audio(url: str, dest: Path) -> str:
    """Return 'skipped' | 'downloaded' | 'failed' | 'no_url'.

    Skips when a non-empty file already exists (Decision 5/8). Never persists the
    URL; on failure leaves no zero-byte stub behind so the next run retries.
    """
    if not url:
        return "no_url"
    if dest.exists() and dest.stat().st_size > 0:
        return "skipped"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "plaud-sync"})
        with urllib.request.urlopen(req, timeout=DOWNLOAD_TIMEOUT) as resp, open(tmp, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        if tmp.stat().st_size == 0:
            tmp.unlink(missing_ok=True)
            return "failed"
        tmp.replace(dest)
        return "downloaded"
    except Exception:
        tmp.unlink(missing_ok=True)
        return "failed"


# --------------------------------------------------------------------------- #
# subcommands
# --------------------------------------------------------------------------- #
def _is_complete(root: Path, folder_rel: str, rec: object) -> bool:
    """A recording is complete when its note exists and either the audio is
    present, or the checkpoint records there is no audio to fetch
    (audio_status 'no_url') — so a genuine no-audio recording converges instead
    of being re-synced forever, while a failed download still retries."""
    folder = plaud_dir(root) / folder_rel
    if not (folder / NOTE_NAME).is_file():
        return False
    audio = folder / AUDIO_NAME
    if audio.is_file() and audio.stat().st_size > 0:
        return True
    return isinstance(rec, dict) and rec.get("audio_status") == "no_url"


def cmd_diff(root: Path) -> int:
    payload = read_stdin_json()
    items = payload.get("data") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        die("list_files JSON has no 'data' array")
    ckpt = load_checkpoint(root)
    recs = ckpt.get("recordings", {})
    taken = {v.get("folder"): k for k, v in recs.items() if isinstance(v, dict)}

    to_sync, skipped = [], []
    for it in items:
        if not isinstance(it, dict) or not it.get("id"):
            continue
        rec_id = it["id"]
        known = recs.get(rec_id)
        folder_rel = known.get("folder") if isinstance(known, dict) and known.get("folder") else folder_for(it, rec_id, taken)
        taken[folder_rel] = rec_id  # reserve so a same-day/same-name sibling gets suffixed
        complete = rec_id in recs and _is_complete(root, folder_rel, known)
        entry = {"id": rec_id, "name": it.get("name", ""), "folder": folder_rel}
        if complete:
            skipped.append(entry)
        else:
            entry["reason"] = "novo" if rec_id not in recs else "incompleto"
            to_sync.append(entry)

    json.dump(
        {"to_sync": to_sync, "skipped": skipped,
         "counts": {"to_sync": len(to_sync), "skipped": len(skipped), "total": len(items)}},
        sys.stdout, ensure_ascii=False, indent=2,
    )
    sys.stdout.write("\n")
    return 0


def cmd_save(root: Path) -> int:
    payload = read_stdin_json()
    if not isinstance(payload, dict) or not payload.get("id"):
        die("get_file JSON is missing an 'id'")
    rec_id = payload["id"]

    ckpt = load_checkpoint(root)
    recs = ckpt.setdefault("recordings", {})
    taken = {v.get("folder"): k for k, v in recs.items() if isinstance(v, dict)}
    known = recs.get(rec_id)
    folder_rel = known.get("folder") if isinstance(known, dict) and known.get("folder") else folder_for(payload, rec_id, taken)
    folder = plaud_dir(root) / folder_rel
    folder.mkdir(parents=True, exist_ok=True)

    audio_status = download_audio(payload.get("presigned_url") or "", folder / AUDIO_NAME)
    audio_present = (folder / AUDIO_NAME).is_file() and (folder / AUDIO_NAME).stat().st_size > 0

    sections = extract_sections(payload)
    (folder / NOTE_NAME).write_text(render_note(payload, sections, audio_present), encoding="utf-8")

    recs[rec_id] = {
        "name": payload.get("name", ""),
        "created_at": payload.get("created_at", ""),
        "start_at": payload.get("start_at", ""),
        "folder": folder_rel,
        "synced_at": now_iso(),
        "has_audio": audio_present,
        "audio_status": audio_status,  # downloaded|skipped|failed|no_url (drives retry vs. converge)
    }
    write_checkpoint(root, ckpt)

    print(json.dumps(
        {"id": rec_id, "folder": folder_rel, "wrote_md": True,
         "audio": audio_status, "has_audio": audio_present},
        ensure_ascii=False,
    ))
    return 0


def cmd_finalize(root: Path, rebuild: bool, user_id: str, user_nickname: str) -> int:
    ckpt = load_checkpoint(root)
    recs = ckpt.setdefault("recordings", {})

    if rebuild:  # drop records whose folder no longer exists on disk (sync-all)
        for rec_id in list(recs):
            rec = recs[rec_id]
            folder_rel = rec.get("folder") if isinstance(rec, dict) else None
            if not folder_rel or not (plaud_dir(root) / folder_rel / NOTE_NAME).is_file():
                del recs[rec_id]

    created = [r.get("created_at") for r in recs.values() if isinstance(r, dict) and r.get("created_at")]
    ckpt["version"] = CHECKPOINT_VERSION
    ckpt["last_synced_at"] = now_iso()
    ckpt["last_created_at"] = max(created) if created else None
    if user_id or user_nickname:
        ckpt["user"] = {"id": user_id, "nickname": user_nickname}
    elif "user" not in ckpt:
        ckpt["user"] = None
    write_checkpoint(root, ckpt)

    print(json.dumps(
        {"finalized": True, "recordings": len(recs),
         "last_created_at": ckpt["last_created_at"], "rebuilt": rebuild},
        ensure_ascii=False,
    ))
    return 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: list) -> int:
    parser = argparse.ArgumentParser(prog="plaud_sync", description="Plaud sync engine")
    # --root is accepted both before and after the subcommand (git-style or
    # modern-style). The main parser supplies the default; subparsers use
    # SUPPRESS so an absent --root after the subcommand doesn't clobber a value
    # given before it.
    parser.add_argument("--root", default=".", help="project dir holding .plaud/ (default: cwd)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    def add_root(p):
        p.add_argument("--root", default=argparse.SUPPRESS, help="project dir holding .plaud/ (default: cwd)")

    add_root(sub.add_parser("diff", help="list_files JSON on stdin -> ids needing sync"))
    add_root(sub.add_parser("save", help="get_file JSON on stdin -> write note + audio + checkpoint"))
    fin = sub.add_parser("finalize", help="update checkpoint top-level fields")
    add_root(fin)
    fin.add_argument("--rebuild", action="store_true", help="prune records with no folder on disk")
    fin.add_argument("--user-id", default="")
    fin.add_argument("--user-nickname", default="")

    args = parser.parse_args(argv)
    root = Path(getattr(args, "root", ".")).resolve()

    if args.cmd == "diff":
        return cmd_diff(root)
    if args.cmd == "save":
        return cmd_save(root)
    if args.cmd == "finalize":
        return cmd_finalize(root, args.rebuild, args.user_id, args.user_nickname)
    die(f"unknown command: {args.cmd}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
