#!/usr/bin/env python3
"""Teste offline dos scripts determinísticos do plugin sdd.

Exercita tech_debt.py e sdd_status.py como subprocessos — exatamente como as
skills os chamam — num diretório temporário. Exit 0 = pass. Só stdlib.

    python3 plugins/sdd/scripts/tests/test_sdd_scripts.py
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent
TECH_DEBT = SCRIPTS / "tech_debt.py"
STATUS = SCRIPTS / "sdd_status.py"

FAILURES = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  {'ok' if ok else 'FALHOU'}  {label}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILURES.append(label)


def run(script: Path, args: list, cwd: Path) -> "subprocess.CompletedProcess":
    return subprocess.run(
        [sys.executable, str(script)] + args,
        cwd=str(cwd), capture_output=True, text=True,
    )


def test_tech_debt(tmp: Path) -> None:
    print("tech_debt.py")
    r = run(TECH_DEBT, [
        "add", "--item", "classe X fora do padrão de DI | com pipe", "--onde", "src/x.py",
        "--motivo", "fora do escopo do sprint 2", "--origem", "sprint 2",
        "--severidade", "media", "--escopo", "amplo",
    ], tmp)
    debt = tmp / "TECH_DEBT.md"
    check("add cria o arquivo a partir do template", r.returncode == 0 and debt.is_file(), r.stderr)
    text = debt.read_text(encoding="utf-8")
    check("item #1 registrado", "| 1 |" in text and "#1" in r.stdout, r.stdout + r.stderr)
    check("pipe escapado preserva a tabela", "\\|" in text and "com pipe" in text)

    r = run(TECH_DEBT, [
        "add", "--item", "bug pré-existente no parser", "--onde", "src/parser.py",
        "--motivo", "achado incidental", "--origem", "review de 2026-07-31",
        "--severidade", "alta", "--escopo", "pontual",
    ], tmp)
    check("numeração incremental (#2)", r.returncode == 0 and "#2" in r.stdout, r.stdout + r.stderr)

    r = run(TECH_DEBT, ["list"], tmp)
    check("list mostra os 2 abertos", r.returncode == 0 and "Itens abertos (2)" in r.stdout, r.stdout)

    r = run(TECH_DEBT, ["resolve", "1", "--ref", "sprint 5 / commit abc1234"], tmp)
    text = debt.read_text(encoding="utf-8")
    aberto = text.split("## Itens resolvidos")[0]
    check("resolve move #1 para resolvidos", r.returncode == 0 and "| 1 |" not in aberto and "abc1234" in text, r.stderr)

    r = run(TECH_DEBT, ["resolve", "99", "--ref", "x"], tmp)
    check("resolve de item inexistente falha (exit != 0)", r.returncode != 0)

    r = run(TECH_DEBT, ["list", "--todos"], tmp)
    check("list --todos mostra 1 aberto + 1 resolvido",
          "Itens abertos (1)" in r.stdout and "Itens resolvidos (1)" in r.stdout, r.stdout)


def test_sdd_status(tmp: Path) -> None:
    print("sdd_status.py")
    base = tmp / "docs" / "sdd"
    sprints = base / "sprints"
    sprints.mkdir(parents=True)
    (sprints / "00-plano.md").write_text("# Plano de Sprints — demo\n", encoding="utf-8")
    (sprints / "01-contrato.md").write_text(
        "# Sprint 01 — Contrato do schema\nStatus: pendente\n\n## Escopo\n- definir schema\n",
        encoding="utf-8",
    )
    (sprints / "02-parser.md").write_text(
        "# Sprint 02 — Parser\nStatus: pendente\n\n## Escopo\n- parser do CSV\n",
        encoding="utf-8",
    )

    r = run(STATUS, ["--dir", "docs/sdd", "render"], tmp)
    status_md = base / "status.md"
    check("render cria status.md", r.returncode == 0 and status_md.is_file(), r.stderr)
    text = status_md.read_text(encoding="utf-8")
    check("painel lista os 2 sprints (e ignora 00-plano)",
          "| 01 |" in text and "| 02 |" in text and "plano" not in text.lower().split("| 01 |")[1])

    r = run(STATUS, ["--dir", "docs/sdd", "set", "1", "em-execucao"], tmp)
    check("set imprime a linha-delta", "Sprint 01: pendente → em-execucao" in r.stdout, r.stdout + r.stderr)
    check("set atualiza o arquivo do sprint",
          "Status: em-execucao" in (sprints / "01-contrato.md").read_text(encoding="utf-8"))
    check("set re-renderiza o painel", "em-execucao" in status_md.read_text(encoding="utf-8"))

    r = run(STATUS, ["--dir", "docs/sdd", "set", "1", "parou", "--nota", "gate: prova não re-executa"], tmp)
    check("nota registrada no sprint e no painel",
          "Nota: gate: prova não re-executa" in (sprints / "01-contrato.md").read_text(encoding="utf-8")
          and "gate: prova não re-executa" in status_md.read_text(encoding="utf-8"), r.stderr)
    check("resumo aponta o sprint parado", "Parado em: 01" in status_md.read_text(encoding="utf-8"))

    r = run(STATUS, ["--dir", "docs/sdd", "set", "1", "status-invalido"], tmp)
    check("status inválido falha (exit != 0)", r.returncode != 0)

    r = run(STATUS, ["--dir", "docs/sdd", "set", "9", "fechado"], tmp)
    check("sprint inexistente falha (exit != 0)", r.returncode != 0)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        test_tech_debt(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_sdd_status(Path(td))
    if FAILURES:
        print(f"\n{len(FAILURES)} caso(s) falharam: {', '.join(FAILURES)}")
        return 1
    print("\ntodos os casos passaram")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
