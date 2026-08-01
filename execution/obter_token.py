#!/usr/bin/env python3
"""
Gera o par IG_USER_ID + IG_ACCESS_TOKEN a partir de um token curto do
Graph API Explorer.

Rode isto UMA VEZ no setup inicial. So precisara rodar de novo se o token
for invalidado (troca de senha do Facebook, remocao do app, revisao de
permissoes) - o Page Access Token de longa duracao nao tem data de validade.

A cadeia executada aqui e:
    token curto (1h)  ->  token longo de usuario (60 dias)
                      ->  token de Pagina (nao expira)
                      ->  ID da conta Instagram Business ligada a Pagina

Uso:
    python execution/obter_token.py --token-curto "EAAG..."
"""

import argparse
import os
import sys

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# `or` em vez do default de getenv: uma variavel definida porem VAZIA no .env
# retorna "" e montaria uma URL invalida.
GRAPH_VERSION = os.getenv("GRAPH_API_VERSION") or "v25.0"
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass


class ErroGraph(Exception):
    def __init__(self, endpoint, err):
        self.endpoint = endpoint
        self.err = err
        super().__init__(err.get("message", "erro desconhecido"))


def get(endpoint, **params):
    resp = requests.get(f"{GRAPH_URL}/{endpoint}", params=params, timeout=60)
    dados = resp.json()
    if "error" in dados:
        raise ErroGraph(endpoint, dados["error"])
    return dados


def abortar(erro):
    print(f"\nERRO da Graph API em /{erro.endpoint}:", file=sys.stderr)
    print(f"  {erro.err.get('message')}", file=sys.stderr)
    print(f"  tipo {erro.err.get('type')} / codigo {erro.err.get('code')}",
          file=sys.stderr)
    sys.exit(1)


def paginas_via_business(token):
    """Paginas que pertencem a um portfolio empresarial NAO aparecem em
    /me/accounts. Nesse caso e preciso enumera-las pelos portfolios, o que
    exige a permissao business_management."""
    try:
        negocios = get("me/businesses", fields="id,name",
                       access_token=token).get("data", [])
    except ErroGraph as e:
        if e.err.get("code") in (100, 200, 10):
            return None  # sinaliza "falta business_management"
        raise

    encontradas = []
    for negocio in negocios:
        for aresta in ("owned_pages", "client_pages"):
            try:
                paginas = get(f"{negocio['id']}/{aresta}", fields="id,name",
                              access_token=token).get("data", [])
            except ErroGraph:
                continue
            for pg in paginas:
                pg["_portfolio"] = negocio.get("name", "")
                encontradas.append(pg)
    return encontradas


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--token-curto", required=True,
                   help="Token gerado no Graph API Explorer (validade 1h).")
    args = p.parse_args()

    app_id = os.getenv("META_APP_ID", "").strip()
    app_secret = os.getenv("META_APP_SECRET", "").strip()
    if not app_id or not app_secret:
        print("ERRO: preencha META_APP_ID e META_APP_SECRET no arquivo .env",
              file=sys.stderr)
        return 1

    try:
        print("[1/4] Trocando token curto por token longo de usuario...")
        longo = get("oauth/access_token",
                    grant_type="fb_exchange_token",
                    client_id=app_id,
                    client_secret=app_secret,
                    fb_exchange_token=args.token_curto)["access_token"]
        print("      ok")

        print("[2/4] Buscando Paginas do Facebook...")
        paginas = get("me/accounts", fields="id,name",
                      access_token=longo).get("data", [])

        if paginas:
            print(f"      {len(paginas)} Pagina(s) via /me/accounts")
        else:
            # Caso comum: a Pagina pertence a um portfolio empresarial
            print("      /me/accounts vazio - tentando pelos portfolios...")
            paginas = paginas_via_business(longo)

            if paginas is None:
                print("\n" + "=" * 68, file=sys.stderr)
                print("FALTA A PERMISSAO business_management", file=sys.stderr)
                print("=" * 68, file=sys.stderr)
                print(
                    "\nSua Pagina pertence a um portfolio empresarial, e nesse\n"
                    "caso ela nao aparece em /me/accounts. Para enxerga-la, o\n"
                    "token precisa tambem da permissao business_management.\n\n"
                    "No Explorador da Graph API:\n"
                    "  1. Adicione a permissao  business_management\n"
                    "  2. Clique em Generate Access Token de novo\n"
                    "  3. Autorize (havera uma opcao nova sobre gerenciar o\n"
                    "     portfolio empresarial - marque SIM)\n"
                    "  4. Rode este script novamente com o token novo\n",
                    file=sys.stderr)
                return 1

            if paginas:
                print(f"      {len(paginas)} Pagina(s) via portfolio empresarial")

        if not paginas:
            print("\nERRO: nenhuma Pagina do Facebook encontrada.", file=sys.stderr)
            print("A conta Instagram precisa estar vinculada a uma Pagina que\n"
                  "voce administre. Veja o Passo 0 de\n"
                  "directives/setup_meta_app.md", file=sys.stderr)
            return 1

        if len(paginas) == 1:
            pagina = paginas[0]
        else:
            print("\n      Varias Paginas encontradas:")
            for i, pg in enumerate(paginas, start=1):
                extra = f"  [{pg['_portfolio']}]" if pg.get("_portfolio") else ""
                print(f"      {i}) {pg['name']}  (id {pg['id']}){extra}")
            escolha = input("\n      Numero da Pagina ligada ao Instagram: ").strip()
            try:
                pagina = paginas[int(escolha) - 1]
            except (ValueError, IndexError):
                print("Escolha invalida.", file=sys.stderr)
                return 1

        print(f"      Pagina: {pagina['name']}")

        # O token de Pagina nem sempre vem junto da listagem (nao vem quando a
        # Pagina foi encontrada via portfolio), entao pedimos explicitamente.
        page_token = pagina.get("access_token")
        if not page_token:
            page_token = get(pagina["id"], fields="access_token",
                             access_token=longo)["access_token"]

        print("[3/4] Localizando a conta Instagram Business da Pagina...")
        info = get(pagina["id"],
                   fields="instagram_business_account{id,username}",
                   access_token=page_token)
        conta = info.get("instagram_business_account")
        if not conta:
            print("\nERRO: esta Pagina nao tem conta Instagram Business vinculada.",
                  file=sys.stderr)
            print("Vincule em: Pagina do Facebook > Configuracoes > Contas\n"
                  "vinculadas > Instagram.", file=sys.stderr)
            return 1
        print(f"      Instagram: @{conta.get('username', '?')}  (id {conta['id']})")

        print("[4/4] Conferindo validade do token de Pagina...")
        debug = get("debug_token",
                    input_token=page_token,
                    access_token=f"{app_id}|{app_secret}").get("data", {})
        expira = debug.get("expires_at", 0)
        print("      " + ("NAO expira (correto)" if expira == 0
                          else f"ATENCAO: expira em {expira} (epoch). "
                               "Verifique se o token de usuario era de longa duracao."))

    except ErroGraph as e:
        abortar(e)

    print("\n" + "=" * 68)
    print("Cadastre estes dois valores como GitHub Secrets")
    print("(Settings > Secrets and variables > Actions > New repository secret)")
    print("e tambem no seu arquivo .env local:")
    print("=" * 68)
    print(f"\nIG_USER_ID={conta['id']}")
    print(f"\nIG_ACCESS_TOKEN={page_token}")
    print("\n" + "=" * 68)
    print("NUNCA commite esses valores. O .env ja esta no .gitignore.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
