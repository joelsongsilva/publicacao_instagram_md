#!/usr/bin/env python3
"""
Confere se ha conteudo (legenda + 2 artes) para os proximos N dias.

Roda semanalmente no GitHub Actions. Se faltar material, o job falha e o
GitHub te manda e-mail - assim voce e avisado com dias de antecedencia,
em vez de descobrir no dia em que o post nao sai.

Use tambem localmente depois de subir o material do mes, para conferir se
nao ficou nenhum buraco:

    python execution/conferir_agenda.py --dias 31
"""

import argparse
import csv
import sys
from datetime import timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CSV_PADRAO = RAIZ / "conteudo" / "legendas.csv"
DIR_IMAGENS = RAIZ / "imagens"

# Reaproveita a logica de leitura do script de publicacao
sys.path.insert(0, str(Path(__file__).resolve().parent))
from publicar_carrossel import (  # noqa: E402
    normalizar_data, achar_coluna, hoje_brasilia,
    COLUNAS_DATA, COLUNAS_LEGENDA,
)


def carregar_legendas(caminho):
    """Devolve {data: legenda} para todas as linhas validas do CSV."""
    if not caminho.exists():
        print(f"ERRO: CSV nao encontrado: {caminho}", file=sys.stderr)
        sys.exit(1)

    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        col_data = achar_coluna(leitor.fieldnames or [], COLUNAS_DATA)
        col_leg = achar_coluna(leitor.fieldnames or [], COLUNAS_LEGENDA)
        if not col_data or not col_leg:
            print(f"ERRO: cabecalho sem coluna de data/legenda: {leitor.fieldnames}",
                  file=sys.stderr)
            sys.exit(1)

        mapa = {}
        for linha in leitor:
            data = normalizar_data(linha.get(col_data))
            if data:
                mapa[data] = (linha.get(col_leg) or "").strip()
        return mapa


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=7,
                   help="Quantos dias a frente conferir (padrao 7).")
    p.add_argument("--csv", default=str(CSV_PADRAO))
    args = p.parse_args()

    legendas = carregar_legendas(Path(args.csv))
    inicio = hoje_brasilia()

    print(f"Conferindo {args.dias} dias a partir de {inicio:%d/%m/%Y}\n")

    faltas = []
    for i in range(args.dias):
        dia = inicio + timedelta(days=i)
        chave = dia.strftime("%Y-%m-%d")

        problemas = []
        legenda = legendas.get(chave)
        if legenda is None:
            problemas.append("sem linha no CSV")
        elif not legenda:
            problemas.append("legenda vazia")
        elif len(legenda) > 2200:
            problemas.append(f"legenda com {len(legenda)} caracteres (max 2200)")

        for n in (1, 2):
            if not (DIR_IMAGENS / f"{chave}_{n}.png").exists():
                problemas.append(f"falta arte {chave}_{n}.png")

        if problemas:
            faltas.append((chave, problemas))
            print(f"  {chave}  FALTA: {', '.join(problemas)}")
        else:
            print(f"  {chave}  ok")

    print()
    if faltas:
        print("=" * 60, file=sys.stderr)
        print(f"ATENCAO: {len(faltas)} dia(s) sem material completo.", file=sys.stderr)
        print("Gere o conteudo e as artes conforme:", file=sys.stderr)
        print("  directives/geracao_conteudo_sheets.md", file=sys.stderr)
        print("  directives/canva_bulk_create.md", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1

    print(f"Tudo pronto para os proximos {args.dias} dias.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
