#!/usr/bin/env python3
"""
Publica o carrossel do dia (2 artes + legenda) no Instagram via Graph API oficial.

Fluxo da API (a API do Instagram NAO agenda posts - quem agenda e o cron do
GitHub Actions; este script publica no momento em que e chamado):

  1. Cria um "container filho" para cada imagem  (is_carousel_item=true)
  2. Aguarda cada container ficar com status FINISHED
  3. Cria o "container pai" do tipo CAROUSEL com os filhos + legenda
  4. Aguarda o pai ficar FINISHED
  5. Chama media_publish -> o post vai ao ar

Uso:
    python execution/publicar_carrossel.py --dry-run
    python execution/publicar_carrossel.py
    python execution/publicar_carrossel.py --data 2026-08-15
    python execution/publicar_carrossel.py --data 2026-08-15 --forcar
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime, date
from pathlib import Path

import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # No GitHub Actions as variaveis vem do ambiente, nao do .env


# As legendas tem emoji. O console do Windows usa cp1252 por padrao e
# quebraria ao imprimir - forcamos UTF-8 na saida.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


# --------------------------------------------------------------------------
# Configuracao
# --------------------------------------------------------------------------

RAIZ = Path(__file__).resolve().parent.parent
CSV_PADRAO = RAIZ / "conteudo" / "legendas.csv"
LOG_PUBLICADOS = RAIZ / "logs" / "publicados.csv"

FUSO = "America/Sao_Paulo"
# `or` em vez do default de getenv: uma variavel definida porem VAZIA no .env
# retorna "" e montaria uma URL invalida.
GRAPH_VERSION = os.getenv("GRAPH_API_VERSION") or "v25.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

# Quanto tempo esperar cada container terminar de processar
TIMEOUT_CONTAINER_S = 180
INTERVALO_POLL_S = 5

# Nomes de coluna aceitos no CSV (case-insensitive, sem acento nao importa aqui
# porque comparamos a string exata em minusculas)
COLUNAS_DATA = ("data", "data da publicacao", "data da publicação", "date")
COLUNAS_LEGENDA = ("legenda", "caption", "descricao", "descrição")


class ErroPublicacao(Exception):
    """Falha esperada e explicavel. Aborta sem stack trace ruidoso."""


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def log(msg):
    print(msg, flush=True)


def hoje_brasilia():
    if ZoneInfo is not None:
        try:
            return datetime.now(ZoneInfo(FUSO)).date()
        except Exception:
            # tzdata ausente no sistema - cai no horario local da maquina
            pass
    return date.today()


def normalizar_data(valor):
    """Aceita 2026-08-15, 15/08/2026 ou 15-08-2026 e devolve 'YYYY-MM-DD'."""
    valor = (valor or "").strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(valor, formato).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def achar_coluna(cabecalho, candidatos):
    for nome in cabecalho:
        if nome and nome.strip().lower() in candidatos:
            return nome
    return None


# --------------------------------------------------------------------------
# Leitura do conteudo
# --------------------------------------------------------------------------

def ler_legenda(caminho_csv, data_alvo):
    """Procura no CSV a linha da data e devolve a legenda ja tratada."""
    if not caminho_csv.exists():
        raise ErroPublicacao(
            f"CSV nao encontrado: {caminho_csv}\n"
            "Gere o conteudo do mes conforme directives/geracao_conteudo_sheets.md"
        )

    # utf-8-sig remove o BOM que o Google Sheets coloca no inicio do arquivo
    with open(caminho_csv, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        if not leitor.fieldnames:
            raise ErroPublicacao(f"CSV vazio ou sem cabecalho: {caminho_csv}")

        col_data = achar_coluna(leitor.fieldnames, COLUNAS_DATA)
        col_legenda = achar_coluna(leitor.fieldnames, COLUNAS_LEGENDA)

        if not col_data or not col_legenda:
            raise ErroPublicacao(
                f"O CSV precisa ter uma coluna de data e uma de legenda.\n"
                f"Cabecalho encontrado: {leitor.fieldnames}"
            )

        for linha in leitor:
            if normalizar_data(linha.get(col_data)) == data_alvo:
                legenda = (linha.get(col_legenda) or "").strip()
                if not legenda:
                    raise ErroPublicacao(
                        f"A linha de {data_alvo} existe mas a legenda esta vazia."
                    )
                # O Sheets costuma exportar quebras de linha como \n literal
                return legenda.replace("\\n", "\n")

    raise ErroPublicacao(
        f"Nenhuma linha para a data {data_alvo} em {caminho_csv.name}.\n"
        "Confira se o conteudo do mes ja foi preenchido."
    )


def ja_publicado(data_alvo):
    if not LOG_PUBLICADOS.exists():
        return None
    with open(LOG_PUBLICADOS, encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            if linha.get("data") == data_alvo and linha.get("status") == "publicado":
                return linha.get("post_id", "(id nao registrado)")
    return None


def registrar_publicacao(data_alvo, post_id, permalink):
    LOG_PUBLICADOS.parent.mkdir(parents=True, exist_ok=True)
    novo = not LOG_PUBLICADOS.exists()
    with open(LOG_PUBLICADOS, "a", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f)
        if novo:
            escritor.writerow(["data", "status", "post_id", "permalink", "publicado_em"])
        escritor.writerow([
            data_alvo, "publicado", post_id, permalink,
            datetime.now().astimezone().isoformat(timespec="seconds"),
        ])


# --------------------------------------------------------------------------
# Graph API
# --------------------------------------------------------------------------

def chamar_api(metodo, endpoint, token, **params):
    params["access_token"] = token
    url = f"{GRAPH_URL}/{endpoint}"
    try:
        if metodo == "POST":
            resp = requests.post(url, data=params, timeout=60)
        else:
            resp = requests.get(url, params=params, timeout=60)
    except requests.RequestException as e:
        raise ErroPublicacao(f"Falha de rede ao chamar {endpoint}: {e}")

    try:
        dados = resp.json()
    except ValueError:
        raise ErroPublicacao(
            f"Resposta nao-JSON de {endpoint} (HTTP {resp.status_code}): {resp.text[:300]}"
        )

    if "error" in dados:
        err = dados["error"]
        raise ErroPublicacao(
            f"Erro da Graph API em {endpoint}:\n"
            f"  mensagem : {err.get('message')}\n"
            f"  tipo     : {err.get('type')} (codigo {err.get('code')})\n"
            f"  detalhe  : {err.get('error_user_msg') or err.get('error_subcode', '-')}"
        )
    return dados


def conferir_url_publica(url):
    """A Meta baixa a imagem por HTTP. Se a URL nao for publica, o post falha
    com um erro generico - entao conferimos antes para dar um erro claro."""
    try:
        resp = requests.head(url, timeout=30, allow_redirects=True)
        if resp.status_code == 200:
            return
        # Alguns hosts nao respondem a HEAD; tenta GET parcial
        resp = requests.get(url, timeout=30, stream=True,
                            headers={"Range": "bytes=0-1023"})
        if resp.status_code in (200, 206):
            return
        raise ErroPublicacao(
            f"A arte nao esta acessivel publicamente (HTTP {resp.status_code}):\n  {url}\n"
            "Confira se o arquivo foi commitado em imagens/ e se o repositorio e publico."
        )
    except requests.RequestException as e:
        raise ErroPublicacao(f"Nao consegui acessar a arte:\n  {url}\n  {e}")


def aguardar_container(container_id, token, rotulo):
    """Fica consultando ate o container terminar de processar."""
    limite = time.time() + TIMEOUT_CONTAINER_S
    while time.time() < limite:
        dados = chamar_api("GET", container_id, token,
                           fields="status_code,status")
        status = dados.get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise ErroPublicacao(
                f"{rotulo} falhou no processamento (status {status}): "
                f"{dados.get('status', 'sem detalhes')}"
            )
        log(f"    {rotulo}: {status}... aguardando")
        time.sleep(INTERVALO_POLL_S)

    raise ErroPublicacao(
        f"{rotulo} nao ficou pronto em {TIMEOUT_CONTAINER_S}s. "
        "Tente novamente com --forcar mais tarde."
    )


def publicar(ig_user_id, token, urls_imagens, legenda):
    filhos = []
    for i, url in enumerate(urls_imagens, start=1):
        log(f"  [1/4] Criando container do slide {i}...")
        resp = chamar_api("POST", f"{ig_user_id}/media", token,
                          image_url=url, is_carousel_item="true")
        filhos.append(resp["id"])
        log(f"        container {resp['id']}")

    log("  [2/4] Aguardando processamento dos slides...")
    for i, cid in enumerate(filhos, start=1):
        aguardar_container(cid, token, f"slide {i}")

    log("  [3/4] Criando container do carrossel...")
    pai = chamar_api("POST", f"{ig_user_id}/media", token,
                     media_type="CAROUSEL",
                     children=",".join(filhos),
                     caption=legenda)["id"]
    aguardar_container(pai, token, "carrossel")

    log("  [4/4] Publicando...")
    post_id = chamar_api("POST", f"{ig_user_id}/media_publish", token,
                         creation_id=pai)["id"]

    permalink = ""
    try:
        permalink = chamar_api("GET", post_id, token,
                               fields="permalink").get("permalink", "")
    except ErroPublicacao:
        pass  # O post ja foi ao ar; nao ter o link nao e motivo pra falhar

    return post_id, permalink


def conferir_limite(ig_user_id, token):
    """Informativo: quantos posts ja foram feitos pela API nas ultimas 24h."""
    try:
        dados = chamar_api("GET", f"{ig_user_id}/content_publishing_limit",
                           token, fields="config,quota_usage")
        item = (dados.get("data") or [{}])[0]
        cota = (item.get("config") or {}).get("quota_total", 100)
        log(f"  Cota de publicacao (24h): {item.get('quota_usage', 0)}/{cota}")
    except ErroPublicacao:
        pass  # nao e critico


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Publica o carrossel do dia no Instagram.")
    p.add_argument("--data", help="Data a publicar (YYYY-MM-DD). Padrao: hoje em Brasilia.")
    p.add_argument("--csv", default=str(CSV_PADRAO), help="Caminho do CSV de conteudo.")
    p.add_argument("--dry-run", action="store_true",
                   help="Valida tudo (CSV, artes, token) mas NAO publica.")
    p.add_argument("--forcar", action="store_true",
                   help="Publica mesmo que a data ja conste no log de publicados.")
    args = p.parse_args()

    data_alvo = args.data or hoje_brasilia().strftime("%Y-%m-%d")
    if normalizar_data(data_alvo) != data_alvo:
        raise ErroPublicacao(f"--data invalida: {args.data}. Use YYYY-MM-DD.")

    log("=" * 60)
    log(f"Publicacao Instagram - {data_alvo}" + ("  [DRY-RUN]" if args.dry_run else ""))
    log("=" * 60)

    # --- Trava anti-duplicidade ---------------------------------------
    anterior = ja_publicado(data_alvo)
    if anterior and not args.forcar:
        log(f"Ja publicado em {data_alvo} (post {anterior}). Nada a fazer.")
        log("Use --forcar para publicar novamente mesmo assim.")
        return 0

    # --- Credenciais ---------------------------------------------------
    ig_user_id = os.getenv("IG_USER_ID", "").strip()
    token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    base_url = os.getenv("BASE_URL_IMAGENS", "").strip().rstrip("/")

    if not base_url:
        # No GitHub Actions da pra montar a URL sozinho
        repo = os.getenv("GITHUB_REPOSITORY", "")
        branch = os.getenv("GITHUB_REF_NAME", "main")
        if repo:
            base_url = f"https://raw.githubusercontent.com/{repo}/{branch}/imagens"

    faltando = [n for n, v in (("IG_USER_ID", ig_user_id),
                               ("IG_ACCESS_TOKEN", token),
                               ("BASE_URL_IMAGENS", base_url)) if not v]
    if faltando and not args.dry_run:
        raise ErroPublicacao(
            "Variaveis de ambiente faltando: " + ", ".join(faltando) + "\n"
            "Local: preencha o .env  |  GitHub: cadastre em Settings > Secrets."
        )

    # --- Conteudo ------------------------------------------------------
    legenda = ler_legenda(Path(args.csv), data_alvo)
    log(f"\nLegenda ({len(legenda)} caracteres):")
    log("-" * 60)
    log(legenda[:400] + ("..." if len(legenda) > 400 else ""))
    log("-" * 60)

    if len(legenda) > 2200:
        raise ErroPublicacao(
            f"Legenda com {len(legenda)} caracteres. O Instagram aceita no maximo 2200."
        )

    # --- Artes ---------------------------------------------------------
    urls = [f"{base_url}/{data_alvo}_{n}.png" for n in (1, 2)] if base_url else []
    log("\nArtes:")
    for url in urls:
        log(f"  {url}")
        conferir_url_publica(url)
        log("    OK - acessivel publicamente")

    if not urls:
        log("  (sem BASE_URL_IMAGENS definida - checagem de artes pulada)")

    # --- Publicacao ----------------------------------------------------
    if args.dry_run:
        log("\nDRY-RUN: tudo validado, nada foi publicado.")
        return 0

    log("")
    conferir_limite(ig_user_id, token)
    post_id, permalink = publicar(ig_user_id, token, urls, legenda)
    registrar_publicacao(data_alvo, post_id, permalink)

    log("\n" + "=" * 60)
    log(f"PUBLICADO! post_id={post_id}")
    if permalink:
        log(f"Link: {permalink}")
    log("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ErroPublicacao as e:
        print(f"\nERRO: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrompido.", file=sys.stderr)
        sys.exit(130)
