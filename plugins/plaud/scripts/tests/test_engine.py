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


def run(args, stdin_path=None, stdin_bytes=None):
    if stdin_bytes is None and stdin_path is not None:
        stdin_bytes = stdin_path.read_bytes()
    proc = subprocess.run(
        [sys.executable, str(ENGINE), *args],
        input=stdin_bytes, capture_output=True,
    )
    if proc.returncode != 0:
        print(proc.stderr.decode("utf-8", "replace"))
    return proc


def only_note(root):
    return next((root / ".plaud" / "recordings").glob("*/nota.md"))


def main() -> int:
    # py_compile: the engine imports and parses cleanly
    comp = subprocess.run([sys.executable, "-m", "py_compile", str(ENGINE)], capture_output=True)
    check(comp.returncode == 0, "engine compiles (py_compile)")

    # --root accepted both before and after the subcommand (model may use either)
    with tempfile.TemporaryDirectory() as tmp:
        before = run(["--root", tmp, "diff"], FIX_LIST)
        after = run(["diff", "--root", tmp], FIX_LIST)
        check(before.returncode == 0 and after.returncode == 0, "--root works before and after the subcommand")

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

    # ---- edge cases from the mini-review (each in its own clean root) ----
    def save_obj(root, obj):
        return run(["--root", str(root), "save"], stdin_bytes=json.dumps(obj).encode())

    base = {
        "id": "edge0000", "name": "Reunião de Borda",
        "created_at": "2026-07-15T10:00:00", "start_at": "2026-07-15T09:00:00",
        "serial_number": "888347281686075888", "duration": 1179000,
        "presigned_url": "https://example.invalid/y.mp3?X-Amz-Signature=fake",
        "source_list": [], "note_list": [],
    }

    # #1 newline / frontmatter-injection in name is escaped inline, not leaked
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        save_obj(root, dict(base, id="inj00001", name="Titulo\n---\ninjected: PWNED"))
        md = only_note(root).read_text(encoding="utf-8")
        fences = [ln for ln in md.splitlines() if ln.strip() == "---"]
        check(len(fences) == 2, "frontmatter has exactly two --- fences (no injection leak)")
        check("\\n---\\ninjected" in md, "newline in name escaped inline (\\n)")

    # #3 numeric-looking serial_number stays a quoted string (no precision loss)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        save_obj(root, dict(base, id="numq0001"))
        md = only_note(root).read_text(encoding="utf-8")
        check('serial_number: "888347281686075888"' in md, "numeric serial_number quoted as string")

    # #5 float duration -> duration_ms consistent (not 0)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        save_obj(root, dict(base, id="float001", duration=1179000.0))
        md = only_note(root).read_text(encoding="utf-8")
        check("duration_ms: 1179000" in md, "float duration -> duration_ms=1179000 (not 0)")
        check("duration: 19m39s" in md, "float duration -> human 19m39s")

    # #2 no-audio recording converges (not re-queued forever)
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        obj = dict(base, id="noaud001")
        obj.pop("presigned_url")
        st = json.loads(save_obj(root, obj).stdout.decode() or "{}")
        check(st.get("audio") == "no_url", "save reports no_url when there is no presigned_url")
        run(["--root", str(root), "finalize"])
        lst = {"data": [dict(base, id="noaud001")]}
        diff = json.loads(run(["--root", str(root), "diff"], stdin_bytes=json.dumps(lst).encode()).stdout.decode() or "{}")
        skipped_ids = {e["id"] for e in diff.get("skipped", [])}
        check("noaud001" in skipped_ids, "no-audio recording converges (diff skips it, no perpetual re-sync)")

    # #4 diff assigns distinct folders to two NEW same-day/same-name siblings
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        lst = {"data": [dict(base, id="dupaaaa1"), dict(base, id="dupbbbb2")]}
        diff = json.loads(run(["--root", str(root), "diff"], stdin_bytes=json.dumps(lst).encode()).stdout.decode() or "{}")
        folders = [e["folder"] for e in diff.get("to_sync", [])]
        check(len(folders) == 2 and len(set(folders)) == 2, "diff gives distinct folders to same-day/name siblings")

    print()
    if failures:
        print(f"FAILED ({len(failures)}): " + "; ".join(failures))
        return 1
    print("ALL PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
