#!/usr/bin/env python3
"""Reproducible, offline test for plaud_sync.py.

Runs the engine as a subprocess (exactly how the skill drives it), from a clean
temp dir, and asserts the observable disk effects — including the security
invariant that no signed URL (X-Amz-*) ever lands in nota.md or the checkpoint.

    python3 plugins/plaud/scripts/tests/test_engine.py     # exit 0 = pass
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "plaud_sync.py"
FIX_GET = HERE / "fixture_get_file.json"
FIX_LIST = HERE / "fixture_list_files.json"
REC_ID = "abc123def4567890"

failures = []


def check(cond: bool, label: str) -> None:
    print(("  PASS " if cond else "  FAIL ") + label)
    if not cond:
        failures.append(label)


def run(args, stdin_path=None):
    stdin = stdin_path.read_bytes() if stdin_path else None
    proc = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        input=stdin, capture_output=True,
    )
    if proc.returncode != 0:
        print(proc.stderr.decode("utf-8", "replace"))
    return proc


def main() -> int:
    # py_compile: the engine imports and parses cleanly
    comp = subprocess.run([sys.executable, "-m", "py_compile", str(ENGINE)], capture_output=True)
    check(comp.returncode == 0, "engine compiles (py_compile)")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # 1. save (audio download fails on the fake host — that is fine)
        p = run(["--root", str(root), "save"], FIX_GET)
        check(p.returncode == 0, "save exits 0")

        notes = list((root / ".plaud" / "recordings").glob("*/nota.md"))
        check(len(notes) == 1, "exactly one nota.md written")
        folder = notes[0].parent if notes else None
        check(folder is not None and folder.name.startswith("2026-07-13-"), "folder prefixed with recording date")

        md = notes[0].read_text(encoding="utf-8") if notes else ""
        check(f"id: {REC_ID}" in md, "frontmatter has the recording id")
        check("date: 2026-07-13" in md, "frontmatter has date from start_at")
        check("duration: 19m39s" in md, "frontmatter has human duration")
        check("source: plaud" in md, "frontmatter has source: plaud")
        check("## Resumo" in md and "## Tópicos" in md and "## Transcrição" in md, "body has the three sections")
        check("**Speaker 1**" in md, "transcript renders a speaker")
        check("[1:01:01]" in md, "long timestamp renders as H:MM:SS")
        check("### Informações Gerais" in md, "note headings demoted one level under Resumo")
        check("X-Amz-" not in md, "no signed URL in nota.md (security)")

        # 2. skip-audio: pre-create a non-empty audio.mp3, save again -> skipped
        audio = folder / "audio.mp3"
        audio.write_bytes(b"FAKEAUDIO")
        before = audio.read_bytes()
        p2 = run(["--root", str(root), "save"], FIX_GET)
        status = json.loads(p2.stdout.decode() or "{}")
        check(status.get("audio") == "skipped", "audio skipped when file already exists")
        check(audio.read_bytes() == before, "existing audio.mp3 not overwritten")
        check(status.get("has_audio") is True, "has_audio true once audio present")

        # 3. finalize -> checkpoint reflects the record + watermark
        p3 = run(["--root", str(root), "finalize", "--user-id", "u1", "--user-nickname", "Tester"])
        check(p3.returncode == 0, "finalize exits 0")
        ckpt = json.loads((root / ".plaud" / "checkpoint.json").read_text(encoding="utf-8"))
        check(REC_ID in ckpt.get("recordings", {}), "checkpoint has the recording")
        check(ckpt.get("last_created_at") == "2026-07-13T13:24:37", "watermark = recording created_at")
        check(ckpt.get("user", {}).get("nickname") == "Tester", "checkpoint stores user")

        # 4. diff: known+complete id skipped, unknown id queued
        p4 = run(["--root", str(root), "diff"], FIX_LIST)
        diff = json.loads(p4.stdout.decode() or "{}")
        to_sync_ids = {e["id"] for e in diff.get("to_sync", [])}
        skipped_ids = {e["id"] for e in diff.get("skipped", [])}
        check(REC_ID in skipped_ids, "diff skips the already-synced complete recording")
        check("new999notlocal0001" in to_sync_ids, "diff queues the not-yet-local recording")

        # 5. no signed URL anywhere under .plaud (nota.md OR checkpoint)
        leaked = [
            str(f) for f in (root / ".plaud").rglob("*")
            if f.is_file() and f.suffix in (".md", ".json") and "X-Amz-" in f.read_text(encoding="utf-8", errors="ignore")
        ]
        check(not leaked, "no signed URL persisted anywhere in .plaud")

    print()
    if failures:
        print(f"FAILED ({len(failures)}): " + "; ".join(failures))
        return 1
    print("ALL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
