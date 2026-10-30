#!/usr/bin/env python3
"""Prepara, valida e opcionalmente envia ao GitHub o material de um mês.

Uso comum:
    python execution/preparar_mes.py --mes 2026-11

Com envio ao GitHub após a validação:
    python execution/preparar_mes.py --mes 2026-11 --enviar
"""

import argparse
import calendar
import re
import subprocess
import sys
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
DIR_CONTEUDO = RAIZ / "conteudo"
DIR_IMAGENS = RAIZ / "imagens"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


def executar(comando):
    """Exibe e executa um comando, preservando sua saída e código de erro."""
    print("\n$", " ".join(str(parte) for parte in comando), flush=True)
    resultado = subprocess.run(comando, cwd=RAIZ)
    if resultado.returncode:
        raise RuntimeError(f"Etapa falhou (código {resultado.returncode}).")


def pngs_numerados(pasta):
    return sorted(
        [arquivo for arquivo in pasta.glob("*.png") if arquivo.stem.isdigit()],
        key=lambda arquivo: int(arquivo.stem),
    )


def artes_finais(mes, dias):
    ano, numero_mes = mes.split("-")
    diarios = [DIR_IMAGENS / f"{ano}-{numero_mes}-{dia:02d}.png"
               for dia in range(1, dias + 1)]
    return diarios + [DIR_IMAGENS / f"{mes}_link.png"]


def main():
    parser = argparse.ArgumentParser(
        description="Prepara e valida as publicações mensais do Instagram.")
    parser.add_argument("--mes", required=True,
                        help="Mês no formato AAAA-MM (ex.: 2026-11).")
    parser.add_argument("--origem", default="imagens_canva",
                        help="Pasta com PNGs numerados do Canva (padrão: imagens_canva).")
    parser.add_argument("--enviar", action="store_true",
                        help="Depois de validar, faz commit e push para o GitHub.")
    args = parser.parse_args()

    encontrado = re.fullmatch(r"(\d{4})-(\d{2})", args.mes)
    if not encontrado:
        parser.error("--mes deve estar no formato AAAA-MM (ex.: 2026-11).")

    ano, numero_mes = map(int, encontrado.groups())
    if not 1 <= numero_mes <= 12:
        parser.error("O mês em --mes deve estar entre 01 e 12.")
    dias = calendar.monthrange(ano, numero_mes)[1]

    planilha = DIR_CONTEUDO / f"{args.mes}.xlsx"
    if not planilha.is_file():
        print(f"ERRO: planilha não encontrada: {planilha.relative_to(RAIZ)}",
              file=sys.stderr)
        print(f"Salve-a como conteudo/{args.mes}.xlsx antes de continuar.",
              file=sys.stderr)
        return 1
    print(f"[ok] Planilha encontrada: {planilha.relative_to(RAIZ)}")

    origem = Path(args.origem)
    if not origem.is_absolute():
        origem = RAIZ / origem
    origem_pngs = pngs_numerados(origem) if origem.is_dir() else []
    esperadas = artes_finais(args.mes, dias)
    finais_presentes = [arquivo for arquivo in esperadas if arquivo.is_file()]

    if origem_pngs:
        if finais_presentes:
            print("ERRO: há imagens tanto na pasta de entrada quanto em imagens/.",
                  file=sys.stderr)
            print("Não é seguro decidir quais arquivos devem prevalecer.", file=sys.stderr)
            return 1
        print(f"[ok] Encontrados {len(origem_pngs)} PNGs em "
              f"{origem.relative_to(RAIZ)}.")
        executar([sys.executable, "execution/renomeador_imagens.py",
                  "--dir", str(origem), "--mes", args.mes])
    elif len(finais_presentes) == len(esperadas):
        print("[ok] Artes já estão renomeadas em imagens/; etapa ignorada.")
    else:
        faltam = len(esperadas) - len(finais_presentes)
        print("ERRO: não encontrei PNGs numerados para importar e faltam "
              f"{faltam} arte(s) final(is) em imagens/.", file=sys.stderr)
        print("Extraia o ZIP do Canva em imagens_canva/ e execute novamente.",
              file=sys.stderr)
        return 1

    executar([sys.executable, "execution/conferir_agenda.py", "--dias", str(dias),
              "--inicio", f"{args.mes}-01"])
    print("\n[ok] Material validado para o mês inteiro.")

    if not args.enviar:
        print("Envio ao GitHub não realizado. Para enviar automaticamente, rode:")
        print(f"  python execution/preparar_mes.py --mes {args.mes} --enviar")
        return 0

    executar(["git", "add", str(planilha), *map(str, esperadas)])
    resultado = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=RAIZ)
    if resultado.returncode == 0:
        print("[ok] Nenhum arquivo novo para enviar ao GitHub.")
        return 0
    if resultado.returncode != 1:
        raise RuntimeError("Não foi possível conferir os arquivos preparados para commit.")

    executar(["git", "commit", "-m", f"conteudo de {args.mes}"])
    executar(["git", "pull", "--rebase", "origin", "main"])
    executar(["git", "push", "origin", "main"])
    print("\n[ok] Material enviado ao GitHub.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        sys.exit(1)
