#!/usr/bin/env python3
"""
Renomeia as artes exportadas do Canva para o padrao que a automacao espera.

O Canva exporta `1.png, 2.png, ... 32.png`. A automacao precisa de:

    2026-08-01.png ... 2026-08-31.png   as artes de cada dia
    2026-08_link.png                    o card do link (um so para o mes)

O card do link e a ULTIMA pagina do export (a que vem depois do ultimo dia).
Ele NAO precisa ser duplicado: o publicador usa o mesmo arquivo todos os dias.

Uso:
    python execution/renomeador_imagens.py --dir "C:/caminho/export" --mes 2026-08
    python execution/renomeador_imagens.py --dir ... --mes 2026-08 --destino imagens
"""

import argparse
import calendar
import os
import re
import shutil
import sys
from pathlib import Path

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

RAIZ = Path(__file__).resolve().parent.parent


def numero_do_arquivo(caminho):
    """'12.png' -> 12. Usado para ordenar como o Canva exportou."""
    m = re.search(r"(\d+)", caminho.stem)
    return int(m.group(1)) if m else 0


def main():
    p = argparse.ArgumentParser(
        description="Renomeia as artes do Canva para o padrao da automacao.")
    p.add_argument("--dir", required=True,
                   help="Pasta onde o ZIP do Canva foi extraido (1.png, 2.png...).")
    p.add_argument("--mes", required=True,
                   help="Mes das artes no formato AAAA-MM (ex.: 2026-08).")
    p.add_argument("--destino", default=str(RAIZ / "imagens"),
                   help="Para onde mover os arquivos. Padrao: imagens/")
    p.add_argument("--copiar", action="store_true",
                   help="Copiar em vez de mover (preserva o export original).")
    args = p.parse_args()

    m = re.match(r"^(\d{4})-(\d{2})$", args.mes)
    if not m:
        print("ERRO: --mes deve estar no formato AAAA-MM (ex.: 2026-08)",
              file=sys.stderr)
        return 1
    ano, mes = int(m.group(1)), int(m.group(2))
    dias_no_mes = calendar.monthrange(ano, mes)[1]

    origem = Path(args.dir)
    if not origem.is_dir():
        print(f"ERRO: pasta nao encontrada: {origem}", file=sys.stderr)
        return 1

    destino = Path(args.destino)
    destino.mkdir(parents=True, exist_ok=True)

    arquivos = sorted(
        [f for f in origem.iterdir() if f.suffix.lower() == ".png"],
        key=numero_do_arquivo,
    )
    if not arquivos:
        print(f"ERRO: nenhum PNG em {origem}", file=sys.stderr)
        return 1

    print(f"Mes {args.mes} tem {dias_no_mes} dias.")
    print(f"Encontrados {len(arquivos)} PNGs em {origem}\n")

    if len(arquivos) == dias_no_mes + 1:
        card_link = arquivos[-1]
        artes_diarias = arquivos[:-1]
        print(f"Interpretacao: {dias_no_mes} artes diarias + 1 card de link "
              f"({card_link.name}).\n")
    elif len(arquivos) == dias_no_mes:
        card_link = None
        artes_diarias = arquivos
        print("AVISO: nao ha card de link no export (so as artes diarias).")
        print(f"       Coloque-o manualmente como {args.mes}_link.png,")
        print("       senao a publicacao falha por falta do slide 2.\n")
    else:
        print(f"ERRO: esperava {dias_no_mes} ou {dias_no_mes + 1} imagens, "
              f"encontrei {len(arquivos)}.", file=sys.stderr)
        print("Confira se o export do Canva saiu completo.", file=sys.stderr)
        return 1

    operacao = shutil.copy2 if args.copiar else shutil.move
    verbo = "Copiado" if args.copiar else "Movido"

    for i, arquivo in enumerate(artes_diarias, start=1):
        novo = destino / f"{ano:04d}-{mes:02d}-{i:02d}.png"
        operacao(str(arquivo), str(novo))
        print(f"  {arquivo.name:>8}  ->  {novo.name}")

    if card_link:
        novo = destino / f"{args.mes}_link.png"
        operacao(str(card_link), str(novo))
        print(f"  {card_link.name:>8}  ->  {novo.name}   (usado em todos os dias)")

    total = len(artes_diarias) + (1 if card_link else 0)
    print(f"\n{verbo}s {total} arquivos para {destino}")
    print("\nProximo passo:")
    print(f"  python execution/conferir_agenda.py --dias {dias_no_mes} "
          f"--inicio {args.mes}-01")
    return 0


if __name__ == "__main__":
    sys.exit(main())
