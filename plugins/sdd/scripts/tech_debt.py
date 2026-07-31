#!/usr/bin/env python3
"""Gerencia o TECH_DEBT.md de um projeto de forma determinística.

Parte do plugin sdd: as skills (execute-sprint, review-quality) chamam este
script em vez de reescrever o arquivo — uma linha de Bash no lugar de ler e
reemitir a tabela inteira. O template do arquivo vive aqui dentro; o script
cria o TECH_DEBT.md na primeira adição. Python 3.7+, só stdlib.

Uso:
    python3 tech_debt.py add --item "..." --onde "..." --motivo "..." \
        --origem "sprint 3" --severidade media --escopo pontual [--raiz DIR]
    python3 tech_debt.py resolve 2 --ref "sprint 5 / commit abc1234" [--raiz DIR]
    python3 tech_debt.py list [--todos] [--raiz DIR]

Saída: uma linha de confirmação por operação. Exit 0 = sucesso; 1 = erro
(item inexistente, arquivo malformado). A numeração é estável: itens
resolvidos mantêm o número; o próximo número é sempre max(todos) + 1.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ABERTOS = "## Itens abertos"
RESOLVIDOS = "## Itens resolvidos"

TEMPLATE = """# Débito Técnico

Backlog de itens fora do escopo do trabalho em andamento no momento em que foram
encontrados — refatorações, bugs pré-existentes, inconsistências — que não foram
corrigidos ali por disciplina de escopo fechado. Cada item é uma **entrada candidata a
virar sprint** via `decompose` (fonte = "backlog de débito técnico").

Este arquivo é a fonte de verdade entre sessões: nenhuma skill mantém memória própria
do que encontrou. Se não está aqui, não sobreviveu à sessão que o encontrou.

Mantido pelo script `tech_debt.py` do plugin sdd (`add` / `resolve` / `list`) — pode
ser editado à mão, desde que a estrutura das tabelas seja preservada.

- **Escopo estimado** decide o destino: **pontual** (1 arquivo) é candidato a correção
  incidental na próxima vez que alguém mexer ali; **amplo** (N arquivos/classes) é
  candidato a **sprint dedicado**, nunca corrigido de passagem.
- Itens resolvidos saem de "Itens abertos" e entram em "Itens resolvidos" com a
  referência do sprint/commit — o backlog só é confiável se fecha o que resolveu.

## Itens abertos

| # | Item | Onde | Por que não foi corrigido agora | Origem | Severidade | Escopo estimado |
|---|------|------|----------------------------------|--------|-------------|------------------|

## Itens resolvidos

| # | Item | Resolvido em |
|---|------|--------------|
"""


def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    sys.stderr.write(f"tech_debt: erro: {msg}\n")
    raise SystemExit(1)


def esc(value: str) -> str:
    """Uma célula de tabela markdown: sem pipes crus nem quebras de linha."""
    return " ".join(value.split()).replace("|", "\\|")


def cells(row: str) -> list:
    """Divide uma linha de tabela em células, respeitando pipes escapados."""
    parts = re.split(r"(?<!\\)\|", row.strip())
    return [p.strip() for p in parts[1:-1]]  # descarta as bordas vazias


def load(path: Path) -> list:
    if not path.is_file():
        return TEMPLATE.splitlines()
    return path.read_text(encoding="utf-8").splitlines()


def table_span(lines: list, heading: str, path: Path) -> tuple:
    """(início, fim) das linhas de DADOS da tabela sob `heading` (fim exclusivo)."""
    try:
        h = next(i for i, ln in enumerate(lines) if ln.strip() == heading)
    except StopIteration:
        die(f"seção '{heading}' não encontrada em {path} — arquivo malformado")
    i = h + 1
    while i < len(lines) and not lines[i].lstrip().startswith("|"):
        if lines[i].strip().startswith("## "):
            die(f"tabela ausente sob '{heading}' em {path}")
        i += 1
    if i + 1 >= len(lines):
        die(f"tabela ausente sob '{heading}' em {path}")
    start = i + 2  # pula cabeçalho e separador
    end = start
    while end < len(lines) and lines[end].lstrip().startswith("|"):
        end += 1
    return start, end


def numbers(lines: list, path: Path) -> list:
    nums = []
    for heading in (ABERTOS, RESOLVIDOS):
        start, end = table_span(lines, heading, path)
        for row in lines[start:end]:
            first = cells(row)[0] if cells(row) else ""
            if first.isdigit():
                nums.append(int(first))
    return nums


def cmd_add(args: argparse.Namespace, path: Path) -> None:
    lines = load(path)
    num = max(numbers(lines, path), default=0) + 1
    row = (
        f"| {num} | {esc(args.item)} | {esc(args.onde)} | {esc(args.motivo)} "
        f"| {esc(args.origem)} | {args.severidade} | {args.escopo} |"
    )
    _, end = table_span(lines, ABERTOS, path)
    lines.insert(end, row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"TECH_DEBT.md: item #{num} registrado ({args.escopo}, severidade {args.severidade}): {esc(args.item)}")


def cmd_resolve(args: argparse.Namespace, path: Path) -> None:
    if not path.is_file():
        die(f"{path} não existe — nada a resolver")
    lines = load(path)
    start, end = table_span(lines, ABERTOS, path)
    for i in range(start, end):
        row_cells = cells(lines[i])
        if row_cells and row_cells[0] == str(args.numero):
            item = row_cells[1] if len(row_cells) > 1 else ""
            del lines[i]
            _, r_end = table_span(lines, RESOLVIDOS, path)
            lines.insert(r_end, f"| {args.numero} | {item} | {esc(args.ref)} |")
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            print(f"TECH_DEBT.md: item #{args.numero} resolvido em {esc(args.ref)}: {item}")
            return
    die(f"item #{args.numero} não está em '{ABERTOS[3:]}'")


def cmd_list(args: argparse.Namespace, path: Path) -> None:
    if not path.is_file():
        print("TECH_DEBT.md: inexistente (nenhum item registrado)")
        return
    lines = load(path)
    start, end = table_span(lines, ABERTOS, path)
    rows = [cells(r) for r in lines[start:end]]
    rows = [r for r in rows if r and r[0].isdigit()]
    if not rows:
        print("Itens abertos: nenhum")
    else:
        print(f"Itens abertos ({len(rows)}):")
        for r in rows:
            pad = r + [""] * 7
            print(f"  #{pad[0]} [{pad[5]}/{pad[6]}] {pad[1]} — {pad[2]} (origem: {pad[4]})")
    if args.todos:
        start, end = table_span(lines, RESOLVIDOS, path)
        rows = [cells(r) for r in lines[start:end]]
        rows = [r for r in rows if r and r[0].isdigit()]
        print(f"Itens resolvidos ({len(rows)}):")
        for r in rows:
            pad = r + [""] * 3
            print(f"  #{pad[0]} {pad[1]} — resolvido em {pad[2]}")


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description="Gerencia o TECH_DEBT.md do projeto.")
    parser.add_argument("--raiz", default=".", help="diretório que contém o TECH_DEBT.md (default: cwd)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="registra um item aberto")
    p_add.add_argument("--item", required=True, help="o problema, objetivo e sucinto")
    p_add.add_argument("--onde", required=True, help="arquivo/módulo/classe")
    p_add.add_argument("--motivo", required=True, help="por que não foi corrigido agora")
    p_add.add_argument("--origem", required=True, help="ex.: 'sprint 3', 'review de 2026-07-31'")
    p_add.add_argument("--severidade", required=True, choices=["alta", "media", "média", "baixa"])
    p_add.add_argument("--escopo", required=True, choices=["pontual", "amplo"])

    p_res = sub.add_parser("resolve", help="move um item para 'Itens resolvidos'")
    p_res.add_argument("numero", type=int, help="número do item")
    p_res.add_argument("--ref", required=True, help="sprint/commit que resolveu")

    p_list = sub.add_parser("list", help="lista os itens abertos")
    p_list.add_argument("--todos", action="store_true", help="inclui os resolvidos")

    args = parser.parse_args(argv)
    if getattr(args, "severidade", None) == "média":
        args.severidade = "media"
    path = Path(args.raiz) / "TECH_DEBT.md"
    {"add": cmd_add, "resolve": cmd_resolve, "list": cmd_list}[args.cmd](args, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
