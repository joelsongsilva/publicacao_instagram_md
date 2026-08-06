#!/usr/bin/env python3
"""
Publica o carrossel do dia (2 slides + legenda) no Instagram via Graph API.

Estrutura esperada (ver directives/publicar_instagram.md):

    conteudo/2026-08.xlsx      colunas: dia (1-31) e legenda
    imagens/2026-08-01.png     slide 1 - card da mensagem do dia
    imagens/2026-08_link.png   slide 2 - card do link, o mesmo o mes inteiro

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
import re
import subprocess
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
DIR_CONTEUDO = RAIZ / "conteudo"
DIR_IMAGENS = RAIZ / "imagens"
LOG_PUBLICADOS = RAIZ / "logs" / "publicados.csv"

FUSO = "America/Sao_Paulo"

# `or` em vez do default de getenv: uma variavel definida porem VAZIA no .env
# retorna "" e montaria uma URL invalida.
GRAPH_VERSION = os.getenv("GRAPH_API_VERSION") or "v25.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

# Quanto tempo esperar cada container terminar de processar
TIMEOUT_CONTAINER_S = 180
INTERVALO_POLL_S = 5

LIMITE_LEGENDA = 2200

# O agendador do GitHub Actions atrasa execucoes em horario de pico (medimos
# 50 a 70 min em 08:00 UTC). A estrategia e agendar CEDO e esperar aqui ate a
# hora certa. Se a espera necessaria passar deste teto, assumimos que nao e o
# cenario previsto (ex.: execucao manual fora de hora) e publicamos na hora.
MAX_ESPERA_S = 100 * 60

# Nomes de coluna aceitos (comparados em minusculas, sem espacos nas pontas)
COLUNAS_DIA = ("dia", "day")
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
    valor = str(valor or "").strip()
    if not valor:
        return None
    # Celulas de data do Excel chegam como datetime
    if isinstance(valor, (datetime, date)):
        return valor.strftime("%Y-%m-%d")
    valor = valor.split(" ")[0]  # descarta hora, se houver
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(valor, formato).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def como_inteiro(valor):
    """'1', 1, 1.0 e '01' viram 1. Qualquer outra coisa vira None."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)) and float(valor).is_integer():
        return int(valor)
    m = re.match(r"^\s*(\d{1,2})\s*$", str(valor))
    return int(m.group(1)) if m else None


def achar_coluna(cabecalho, candidatos):
    for nome in cabecalho:
        if nome and str(nome).strip().lower() in candidatos:
            return nome
    return None


# --------------------------------------------------------------------------
# Leitura do conteudo (.xlsx ou .csv)
# --------------------------------------------------------------------------

def achar_arquivo_conteudo(data_alvo, explicito=None):
    """Prioriza o arquivo do mes (2026-08.xlsx), com fallback para um arquivo
    unico acumulando varios meses (legendas.csv)."""
    if explicito:
        caminho = Path(explicito)
        if not caminho.exists():
            raise ErroPublicacao(f"Arquivo de conteudo nao encontrado: {caminho}")
        return caminho

    ano_mes = data_alvo[:7]
    candidatos = [
        DIR_CONTEUDO / f"{ano_mes}.xlsx",
        DIR_CONTEUDO / f"{ano_mes}.csv",
        DIR_CONTEUDO / "legendas.xlsx",
        DIR_CONTEUDO / "legendas.csv",
    ]
    for caminho in candidatos:
        if caminho.exists():
            return caminho

    raise ErroPublicacao(
        f"Nenhum arquivo de conteudo para {ano_mes}.\n"
        "Procurei por:\n  " + "\n  ".join(str(c) for c in candidatos) + "\n"
        "Gere o conteudo do mes conforme directives/geracao_conteudo_sheets.md"
    )


def ler_planilha(caminho):
    """Devolve (cabecalho, registros) de um .xlsx ou .csv."""
    if caminho.suffix.lower() in (".xlsx", ".xlsm"):
        try:
            import openpyxl
        except ImportError:
            raise ErroPublicacao(
                "Para ler .xlsx e preciso o openpyxl:\n"
                "    pip install -r requirements.txt"
            )
        ws = openpyxl.load_workbook(caminho, data_only=True).worksheets[0]
        linhas = list(ws.iter_rows(values_only=True))
        if not linhas:
            raise ErroPublicacao(f"Planilha vazia: {caminho}")
        cabecalho = [str(c).strip() if c is not None else "" for c in linhas[0]]
        registros = [dict(zip(cabecalho, linha)) for linha in linhas[1:]]
        return cabecalho, registros

    # utf-8-sig remove o BOM que o Google Sheets coloca no inicio do arquivo
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.DictReader(f)
        if not leitor.fieldnames:
            raise ErroPublicacao(f"CSV vazio ou sem cabecalho: {caminho}")
        return list(leitor.fieldnames), list(leitor)


def carregar_legendas(caminho):
    """Devolve {'YYYY-MM-DD': legenda} a partir do arquivo.

    Aceita dois formatos de identificacao da linha:
      - coluna `data` com a data completa; ou
      - coluna `dia` (1-31), caso em que o mes vem do NOME do arquivo.
    """
    cabecalho, registros = ler_planilha(caminho)

    col_legenda = achar_coluna(cabecalho, COLUNAS_LEGENDA)
    col_data = achar_coluna(cabecalho, COLUNAS_DATA)
    col_dia = achar_coluna(cabecalho, COLUNAS_DIA)

    if not col_legenda:
        raise ErroPublicacao(
            f"{caminho.name} nao tem coluna de legenda.\n"
            f"Cabecalho encontrado: {cabecalho}"
        )
    if not col_data and not col_dia:
        raise ErroPublicacao(
            f"{caminho.name} precisa de uma coluna `data` (data completa) ou "
            f"`dia` (1-31).\nCabecalho encontrado: {cabecalho}"
        )

    # Com coluna `dia`, o mes so pode vir do nome do arquivo (ex.: 2026-08.xlsx)
    mes_do_arquivo = None
    if col_dia and not col_data:
        m = re.match(r"^(\d{4})-(\d{2})$", caminho.stem)
        if not m:
            raise ErroPublicacao(
                f"{caminho.name} usa a coluna `dia`, entao o nome do arquivo\n"
                f"precisa dizer de que mes ele e: `AAAA-MM{caminho.suffix}`\n"
                f"(ex.: conteudo/2026-08{caminho.suffix}).\n"
                "Renomeie o arquivo ou acrescente uma coluna `data` completa."
            )
        mes_do_arquivo = f"{m.group(1)}-{m.group(2)}"

    legendas = {}
    for linha in registros:
        chave = None
        if col_data:
            chave = normalizar_data(linha.get(col_data))
        if not chave and col_dia and mes_do_arquivo:
            dia = como_inteiro(linha.get(col_dia))
            if dia and 1 <= dia <= 31:
                chave = f"{mes_do_arquivo}-{dia:02d}"
        if not chave:
            continue

        legenda = str(linha.get(col_legenda) or "").strip()
        # O Sheets/Excel costumam guardar quebras de linha como \n literal
        legendas[chave] = legenda.replace("\\n", "\n")

    if not legendas:
        raise ErroPublicacao(
            f"Nenhuma linha valida em {caminho.name}. "
            "Confira as colunas de data/dia."
        )
    return legendas


def ler_legenda(caminho, data_alvo):
    legendas = carregar_legendas(caminho)
    if data_alvo not in legendas:
        raise ErroPublicacao(
            f"Nenhuma linha para {data_alvo} em {caminho.name}.\n"
            "Confira se o conteudo do mes ja foi preenchido."
        )
    legenda = legendas[data_alvo]
    if not legenda:
        raise ErroPublicacao(f"A linha de {data_alvo} existe mas a legenda esta vazia.")
    return legenda


# --------------------------------------------------------------------------
# Resolucao das artes
# --------------------------------------------------------------------------

def resolver_imagens(data_alvo):
    """Devolve os nomes dos arquivos dos dois slides.

    Slide 1: a arte do dia.
    Slide 2: o card do link. Normalmente e um so para o mes inteiro, mas um
             arquivo especifico do dia tem prioridade se existir.
    """
    ano_mes = data_alvo[:7]

    opcoes_slide1 = [f"{data_alvo}.png", f"{data_alvo}_1.png"]
    opcoes_slide2 = [f"{data_alvo}_2.png", f"{ano_mes}_link.png", "card_link.png"]

    def primeiro_existente(opcoes):
        for nome in opcoes:
            if (DIR_IMAGENS / nome).exists():
                return nome
        return None

    slide1 = primeiro_existente(opcoes_slide1)
    if not slide1:
        raise ErroPublicacao(
            f"Arte do dia {data_alvo} nao encontrada em imagens/.\n"
            "Procurei por: " + ", ".join(opcoes_slide1)
        )

    slide2 = primeiro_existente(opcoes_slide2)
    if not slide2:
        raise ErroPublicacao(
            f"Card do link nao encontrado em imagens/.\n"
            "Procurei por: " + ", ".join(opcoes_slide2) + "\n"
            f"Coloque o card do mes como imagens/{ano_mes}_link.png"
        )

    return [slide1, slide2]


def ja_publicado(data_alvo):
    if not LOG_PUBLICADOS.exists():
        return None
    with open(LOG_PUBLICADOS, encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f):
            if linha.get("data") == data_alvo and linha.get("status") == "publicado":
                return linha.get("post_id", "(id nao registrado)")
    return None


def atualizar_log_do_git():
    """Traz o commit mais recente de logs/publicados.csv antes da checagem
    final anti-duplicidade.

    Existe porque o `concurrency` do GitHub Actions e o unico obstaculo entre
    o checkout desta execucao e outra execucao paralela publicando o mesmo
    dia - e ja falhou em prevenir duplicidade (dois posts saíram com 36s de
    diferenca em 2026-08-05). A checagem em `main()` acontece logo no inicio,
    antes de ate 83 min de espera (`--aguardar-ate`); sem atualizar o log
    aqui, a checagem inicial fica obsoleta bem antes da publicacao de fato.
    Best-effort: se nao houver git/rede, segue com o log que ja tem em disco.
    """
    try:
        subprocess.run(
            ["git", "-C", str(RAIZ), "pull", "--ff-only", "--quiet"],
            timeout=30, capture_output=True, check=False,
        )
    except (OSError, subprocess.SubprocessError):
        pass


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
        dados = chamar_api("GET", container_id, token, fields="status_code,status")
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


def aguardar_ate(hora_alvo):
    """Segura a publicacao ate `hora_alvo` (HH:MM no fuso de Brasilia).

    Existe porque o cron do GitHub Actions e impreciso: agendamos com folga e
    e aqui que a pontualidade e recuperada. Se ja passou da hora, publica
    imediatamente - atrasado e melhor que nao publicado.
    """
    m = re.match(r"^([01]?\d|2[0-3]):([0-5]\d)$", hora_alvo.strip())
    if not m:
        raise ErroPublicacao(f"--aguardar-ate invalido: {hora_alvo}. Use HH:MM.")
    hora, minuto = int(m.group(1)), int(m.group(2))

    tz = ZoneInfo(FUSO) if ZoneInfo else None
    try:
        agora = datetime.now(tz)
    except Exception:
        agora = datetime.now()

    alvo = agora.replace(hour=hora, minute=minuto, second=0, microsecond=0)
    espera = (alvo - agora).total_seconds()

    if espera <= 0:
        log(f"  Horario alvo {hora_alvo} ja passou (agora {agora:%H:%M}). "
            f"Publicando com {abs(int(espera)) // 60} min de atraso.")
        return

    if espera > MAX_ESPERA_S:
        log(f"  Faltam {int(espera) // 60} min para {hora_alvo} - espera longa "
            "demais para ser o cron diario. Publicando agora.")
        return

    log(f"  Agora sao {agora:%H:%M}. Aguardando {int(espera) // 60} min "
        f"{int(espera) % 60}s ate {hora_alvo}...")
    time.sleep(espera)
    log("  Hora certa. Publicando.")


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
    p.add_argument("--conteudo", help="Caminho do .xlsx/.csv. Padrao: conteudo/AAAA-MM.xlsx")
    p.add_argument("--dry-run", action="store_true",
                   help="Valida tudo (conteudo, artes, token) mas NAO publica.")
    p.add_argument("--forcar", action="store_true",
                   help="Publica mesmo que a data ja conste no log de publicados.")
    p.add_argument("--aguardar-ate", metavar="HH:MM",
                   help="Valida tudo e so entao aguarda ate este horario de "
                        "Brasilia para publicar. Compensa o atraso do cron do "
                        "GitHub Actions. Ignorado se a hora ja passou.")
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
    base_url = (os.getenv("BASE_URL_IMAGENS") or "").strip().rstrip("/")

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
    arquivo = achar_arquivo_conteudo(data_alvo, args.conteudo)
    log(f"\nConteudo: {arquivo.name}")
    legenda = ler_legenda(arquivo, data_alvo)
    log(f"Legenda ({len(legenda)} caracteres):")
    log("-" * 60)
    log(legenda[:400] + ("..." if len(legenda) > 400 else ""))
    log("-" * 60)

    if len(legenda) > LIMITE_LEGENDA:
        raise ErroPublicacao(
            f"Legenda com {len(legenda)} caracteres. "
            f"O Instagram aceita no maximo {LIMITE_LEGENDA}."
        )

    # --- Artes ---------------------------------------------------------
    nomes = resolver_imagens(data_alvo)
    log("\nArtes:")
    urls = []
    for i, nome in enumerate(nomes, start=1):
        if base_url:
            url = f"{base_url}/{nome}"
            log(f"  slide {i}: {url}")
            conferir_url_publica(url)
            log("           OK - acessivel publicamente")
            urls.append(url)
        else:
            log(f"  slide {i}: {nome}  (local OK; sem BASE_URL_IMAGENS para checar)")

    # --- Publicacao ----------------------------------------------------
    if args.dry_run:
        if args.aguardar_ate:
            log(f"\n(fora do dry-run, aguardaria ate {args.aguardar_ate} "
                "antes de publicar)")
        log("\nDRY-RUN: tudo validado, nada foi publicado.")
        return 0

    # A espera vem DEPOIS da validacao: se algo estiver errado, e melhor
    # descobrir agora do que depois de uma hora parado.
    log("")
    if args.aguardar_ate:
        aguardar_ate(args.aguardar_ate)

    # --- Trava anti-duplicidade, de novo ------------------------------
    # A checagem la em cima pode ter ate 83 min de defasagem (a espera de
    # --aguardar-ate). Atualiza o log a partir do git e confere outra vez,
    # bem antes de chamar a API, para fechar essa janela.
    if not args.forcar:
        atualizar_log_do_git()
        anterior = ja_publicado(data_alvo)
        if anterior:
            log(f"\nJa publicado em {data_alvo} (post {anterior}) por outra "
                "execucao enquanto esta aguardava. Abortando para evitar "
                "duplicidade.")
            return 0

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
