#!/usr/bin/env python3
"""
Confere se ha conteudo (legenda + as duas artes) para os proximos N dias.

Roda semanalmente no GitHub Actions. Se faltar material, o job falha e o
GitHub te manda e-mail - assim voce e avisado com dias de antecedencia,
em vez de descobrir no dia em que o post nao sai.

Use tambem localmente depois de subir o material do mes:

    python execution/conferir_agenda.py --dias 31 --inicio 2026-08-01
"""

import argparse
import sys
from datetime import timedelta, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Reaproveita a logica de leitura do script de publicacao
sys.path.insert(0, str(Path(__file__).resolve().parent))
from publicar_carrossel import (  # noqa: E402
    achar_arquivo_conteudo, carregar_legendas, resolver_imagens,
    hoje_brasilia, normalizar_data, ErroPublicacao, LIMITE_LEGENDA,
)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dias", type=int, default=7,
                   help="Quantos dias conferir (padrao 7).")
    p.add_argument("--inicio", help="Data inicial YYYY-MM-DD. Padrao: hoje.")
    p.add_argument("--conteudo", help="Caminho do .xlsx/.csv especifico.")
    args = p.parse_args()

    if args.inicio:
        inicio_str = normalizar_data(args.inicio)
        if not inicio_str:
            print(f"ERRO: --inicio invalido: {args.inicio}", file=sys.stderr)
            return 1
        inicio = datetime.strptime(inicio_str, "%Y-%m-%d").date()
    else:
        inicio = hoje_brasilia()

    print(f"Conferindo {args.dias} dias a partir de {inicio:%d/%m/%Y}\n")

    # Cache por arquivo: o intervalo pode atravessar a virada do mes
    cache_legendas = {}

    def legendas_do_dia(chave):
        try:
            arquivo = achar_arquivo_conteudo(chave, args.conteudo)
        except ErroPublicacao as e:
            return None, str(e).split("\n")[0]
        if arquivo not in cache_legendas:
            try:
                cache_legendas[arquivo] = carregar_legendas(arquivo)
            except ErroPublicacao as e:
                return None, str(e).split("\n")[0]
        return cache_legendas[arquivo], None

    faltas = []
    for i in range(args.dias):
        dia = inicio + timedelta(days=i)
        chave = dia.strftime("%Y-%m-%d")
        problemas = []

        legendas, erro = legendas_do_dia(chave)
        if erro:
            problemas.append(erro)
        else:
            legenda = legendas.get(chave)
            if legenda is None:
                problemas.append("sem linha no arquivo de conteudo")
            elif not legenda:
                problemas.append("legenda vazia")
            elif len(legenda) > LIMITE_LEGENDA:
                problemas.append(f"legenda com {len(legenda)} caracteres "
                                 f"(max {LIMITE_LEGENDA})")

        try:
            resolver_imagens(chave)
        except ErroPublicacao as e:
            problemas.append(str(e).split("\n")[0])

        if problemas:
            faltas.append(chave)
            print(f"  {chave}  FALTA: {'; '.join(problemas)}")
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

    print(f"Tudo pronto para os {args.dias} dias conferidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
