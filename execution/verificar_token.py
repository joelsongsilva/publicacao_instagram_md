#!/usr/bin/env python3
"""
Confere se o IG_ACCESS_TOKEN continua valido e se a conta responde.

Roda semanalmente no GitHub Actions. Se falhar, o GitHub manda e-mail -
assim voce descobre que o token morreu ANTES de perder uma publicacao,
e nao no dia seguinte olhando o perfil.

Uso:
    python execution/verificar_token.py
"""

import os
import sys
from datetime import datetime, timezone

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

GRAPH_VERSION = os.getenv("GRAPH_API_VERSION", "v25.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}"

# Avisa com esta antecedencia se o token tiver data de validade
DIAS_DE_AVISO = 14


def get(endpoint, **params):
    resp = requests.get(f"{GRAPH_URL}/{endpoint}", params=params, timeout=60)
    dados = resp.json()
    if "error" in dados:
        err = dados["error"]
        raise RuntimeError(f"{err.get('message')} "
                           f"(tipo {err.get('type')}, codigo {err.get('code')})")
    return dados


def main():
    token = os.getenv("IG_ACCESS_TOKEN", "").strip()
    ig_user_id = os.getenv("IG_USER_ID", "").strip()
    app_id = os.getenv("META_APP_ID", "").strip()
    app_secret = os.getenv("META_APP_SECRET", "").strip()

    if not token or not ig_user_id:
        print("ERRO: IG_ACCESS_TOKEN e/ou IG_USER_ID nao definidos.", file=sys.stderr)
        return 1

    problemas = []

    # 1. O teste que realmente importa: a conta responde com este token?
    print("[1/2] Testando acesso a conta Instagram...")
    try:
        conta = get(ig_user_id, fields="username,name", access_token=token)
        print(f"      OK - conectado a @{conta.get('username', '?')}")
    except RuntimeError as e:
        print(f"      FALHOU - {e}")
        problemas.append("O token nao consegue mais acessar a conta. "
                         "Rode: python execution/obter_token.py --token-curto ...")

    # 2. Validade formal (so da pra checar se temos app id/secret)
    print("[2/2] Inspecionando o token...")
    if app_id and app_secret:
        try:
            d = get("debug_token", input_token=token,
                    access_token=f"{app_id}|{app_secret}").get("data", {})
            if not d.get("is_valid"):
                problemas.append(f"Token marcado como invalido: {d.get('error', {})}")
            expira = d.get("expires_at", 0)
            if expira == 0:
                print("      OK - token sem data de expiracao")
            else:
                dt = datetime.fromtimestamp(expira, tz=timezone.utc)
                dias = (dt - datetime.now(timezone.utc)).days
                print(f"      Expira em {dt:%d/%m/%Y} ({dias} dias)")
                if dias <= DIAS_DE_AVISO:
                    problemas.append(
                        f"O token expira em {dias} dias. Gere um novo com "
                        "execution/obter_token.py e atualize o GitHub Secret."
                    )
            escopos = d.get("scopes", [])
            faltando = [s for s in ("instagram_basic", "instagram_content_publish")
                        if s not in escopos]
            if faltando:
                problemas.append(f"Permissoes faltando no token: {faltando}")
            else:
                print("      OK - permissoes de publicacao presentes")
        except RuntimeError as e:
            print(f"      Nao consegui inspecionar: {e}")
    else:
        print("      Pulado (META_APP_ID/META_APP_SECRET nao definidos)")

    print()
    if problemas:
        print("=" * 60, file=sys.stderr)
        print("ATENCAO - acao necessaria:", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        return 1

    print("Tudo certo. Publicacoes seguem funcionando.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
