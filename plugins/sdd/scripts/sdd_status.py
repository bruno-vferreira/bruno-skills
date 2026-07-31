#!/usr/bin/env python3
"""Painel do ciclo run-sprints, derivado dos arquivos de sprint.

Parte do plugin sdd. O estado de cada sprint vive no próprio arquivo
(`docs/sdd/sprints/NN-*.md`, linha `Status:`); este script atualiza essa linha
e re-renderiza o painel `docs/sdd/status.md` — uma chamada de Bash no lugar de
o modelo reescrever tabelas. Python 3.7+, só stdlib.

Uso:
    python3 sdd_status.py render [--dir docs/sdd]
    python3 sdd_status.py set 3 em-execucao [--nota "..."] [--dir docs/sdd]

Status permitidos: pendente, em-execucao, executado (implementado, gate
pendente), conforme (gate passou, mini review pendente), fechado, parou.
`set` imprime a linha-delta ("Sprint 03: pendente → em-execucao") — é ela que
vai para a conversa; o painel completo fica no arquivo. Exit 0 = sucesso.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

STATUSES = ["pendente", "em-execucao", "executado", "conforme", "fechado", "parou"]
_NUM = re.compile(r"^(\d+)-")
_STATUS = re.compile(r"^Status:\s*(\S+)\s*$")
_NOTA = re.compile(r"^Nota:\s*(.*)$")


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.stderr.write(f"sdd_status: erro: {msg}\n")
    raise SystemExit(1)


def sprint_files(base: Path) -> list:
    sprints = base / "sprints"
    if not sprints.is_dir():
        die(f"{sprints} não existe — a decompose grava o plano lá")
    files = []
    for p in sorted(sprints.glob("*.md")):
        m = _NUM.match(p.name)
        if m and int(m.group(1)) > 0:  # 00-plano.md é o índice, não um sprint
            files.append((int(m.group(1)), p))
    if not files:
        die(f"nenhum arquivo de sprint NN-*.md em {sprints}")
    return files


def parse(path: Path) -> dict:
    title, status, nota = path.stem, "pendente", ""
    for ln in path.read_text(encoding="utf-8").splitlines():
        if ln.startswith("# ") and title == path.stem:
            title = ln[2:].strip()
        m = _STATUS.match(ln)
        if m:
            status = m.group(1)
        m = _NOTA.match(ln)
        if m:
            nota = m.group(1).strip()
    return {"title": title, "status": status, "nota": nota}


def render(base: Path) -> None:
    rows = []
    counts = {}
    stopped = []
    for num, path in sprint_files(base):
        info = parse(path)
        counts[info["status"]] = counts.get(info["status"], 0) + 1
        if info["status"] == "parou":
            stopped.append(f"{num:02d}")
        rows.append(f"| {num:02d} | {info['title']} | {info['status']} | {info['nota']} |")
    total = len(rows)
    resumo = " · ".join(f"{counts[s]} {s}" for s in STATUSES if s in counts)
    parado = ", ".join(stopped) if stopped else "nenhum"
    out = "\n".join(
        [
            "# Painel — ciclo SDD",
            "",
            "Gerado por `sdd_status.py render` a partir de `sprints/NN-*.md` — não edite a",
            "tabela à mão; atualize o status com `sdd_status.py set`.",
            "",
            "| # | Sprint | Status | Nota |",
            "|---|--------|--------|------|",
            *rows,
            "",
            f"**Resumo:** {total} sprint(s) — {resumo}. Parado em: {parado}.",
            "",
        ]
    )
    (base / "status.md").write_text(out, encoding="utf-8")


def cmd_set(args: argparse.Namespace, base: Path) -> None:
    target = next((p for num, p in sprint_files(base) if num == args.numero), None)
    if target is None:
        die(f"sprint {args.numero:02d} não encontrado em {base / 'sprints'}")
    lines = target.read_text(encoding="utf-8").splitlines()
    old = "pendente"
    status_at = None
    for i, ln in enumerate(lines):
        m = _STATUS.match(ln)
        if m:
            old, status_at = m.group(1), i
            break
    if status_at is None:
        die(f"{target} não tem linha 'Status:' — plano fora do formato da decompose")
    lines[status_at] = f"Status: {args.status}"
    if args.nota is not None:
        nota_at = next((i for i, ln in enumerate(lines) if _NOTA.match(ln)), None)
        if args.nota == "":
            if nota_at is not None:
                del lines[nota_at]
        elif nota_at is not None:
            lines[nota_at] = f"Nota: {args.nota}"
        else:
            lines.insert(status_at + 1, f"Nota: {args.nota}")
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    render(base)
    delta = f"Sprint {args.numero:02d}: {old} → {args.status}"
    if args.nota:
        delta += f" ({args.nota})"
    print(delta)


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="Painel do ciclo run-sprints em docs/sdd/.")
    parser.add_argument("--dir", default="docs/sdd", help="diretório do ciclo (default: docs/sdd)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("render", help="re-renderiza status.md a partir dos arquivos de sprint")

    p_set = sub.add_parser("set", help="atualiza o status de um sprint e re-renderiza o painel")
    p_set.add_argument("numero", type=int, help="número do sprint (ex.: 3)")
    p_set.add_argument("status", choices=STATUSES)
    p_set.add_argument("--nota", default=None, help="motivo/observação ('' remove a nota)")

    args = parser.parse_args(argv)
    base = Path(args.dir)
    if args.cmd == "render":
        render(base)
        print(f"{base / 'status.md'} atualizado")
    else:
        cmd_set(args, base)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
