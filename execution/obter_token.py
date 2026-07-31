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

GRAPH_VERSION = os.getenv("GRAPH_API_VERSION", "v25.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"


def get(endpoint, **params):
    resp = requests.get(f"{GRAPH_URL}/{endpoint}", params=params, timeout=60)
    dados = resp.json()
    if "error" in dados:
        err = dados["error"]
        print(f"\nERRO da Graph API em /{endpoint}:", file=sys.stderr)
        print(f"  {err.get('message')}", file=sys.stderr)
        print(f"  tipo {err.get('type')} / codigo {err.get('code')}", file=sys.stderr)
        sys.exit(1)
    return dados


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

    print("[1/4] Trocando token curto por token longo de usuario...")
    longo = get("oauth/access_token",
                grant_type="fb_exchange_token",
                client_id=app_id,
                client_secret=app_secret,
                fb_exchange_token=args.token_curto)["access_token"]
    print("      ok")

    print("[2/4] Buscando Paginas do Facebook vinculadas...")
    paginas = get("me/accounts", access_token=longo).get("data", [])
    if not paginas:
        print("\nERRO: nenhuma Pagina do Facebook encontrada nesta conta.",
              file=sys.stderr)
        print("A conta Instagram precisa estar vinculada a uma Pagina.",
              file=sys.stderr)
        return 1

    if len(paginas) == 1:
        pagina = paginas[0]
    else:
        print("\n      Varias Paginas encontradas:")
        for i, pg in enumerate(paginas, start=1):
            print(f"      {i}) {pg['name']}  (id {pg['id']})")
        escolha = input("\n      Numero da Pagina ligada ao Instagram: ").strip()
        try:
            pagina = paginas[int(escolha) - 1]
        except (ValueError, IndexError):
            print("Escolha invalida.", file=sys.stderr)
            return 1

    print(f"      Pagina: {pagina['name']}")
    page_token = pagina["access_token"]

    print("[3/4] Localizando a conta Instagram Business da Pagina...")
    info = get(pagina["id"],
               fields="instagram_business_account{id,username}",
               access_token=page_token)
    conta = info.get("instagram_business_account")
    if not conta:
        print("\nERRO: esta Pagina nao tem conta Instagram Business vinculada.",
              file=sys.stderr)
        print("Vincule em: Instagram > Configuracoes > Conta profissional > Pagina.",
              file=sys.stderr)
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
