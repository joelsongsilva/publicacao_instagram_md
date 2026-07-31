# Automação de Publicação no Instagram — Meditação Diária

Publica automaticamente, todo dia às 05:00 (horário de Brasília), um carrossel
de 2 artes com legenda no Instagram. Sem servidor, sem mensalidade, sem Meta
Business Suite.

## Como funciona

```
Conteúdo do mês (IA → CSV)
        ↓
Canva Bulk Create  →  ZIP  →  renomeador_imagens.py  →  imagens/YYYY-MM-DD_{1,2}.png
        ↓
        git push  (uma vez por mês)
        ↓
GitHub Actions — cron diário 05:00 BRT
        ↓
publicar_carrossel.py  →  Graph API oficial  →  post no ar
```

As artes ficam públicas em `raw.githubusercontent.com`, que é de onde a Meta
as baixa na hora de publicar (a API exige URL pública — ela não aceita upload
de arquivo).

## Custo

Zero. GitHub Actions é gratuito e a API de publicação do Instagram também.

## Comece por aqui

| Ordem | O quê | Onde |
|---|---|---|
| 1 (uma vez) | Criar o app Meta e pegar o token | [directives/setup_meta_app.md](directives/setup_meta_app.md) |
| 2 (mensal) | Gerar o conteúdo do mês | [directives/geracao_conteudo_sheets.md](directives/geracao_conteudo_sheets.md) |
| 3 (mensal) | Gerar e renomear as artes | [directives/canva_bulk_create.md](directives/canva_bulk_create.md) |
| 4 (mensal) | Subir e conferir | [directives/publicar_instagram.md](directives/publicar_instagram.md) |

## Estrutura

```
conteudo/legendas.csv     conteúdo do mês (colunas Data + Legenda)
imagens/                  artes renomeadas YYYY-MM-DD_1.png / _2.png
execution/                scripts Python
logs/publicados.csv       o que já foi ao ar (trava anti-duplicidade)
directives/               os passo a passo
.github/workflows/        o agendador
```

## Scripts

```bash
# Validar tudo sem publicar (use sempre antes de confiar)
python execution/publicar_carrossel.py --dry-run

# Publicar um dia específico
python execution/publicar_carrossel.py --data 2026-08-15

# Ver se falta material nos próximos 31 dias
python execution/conferir_agenda.py --dias 31

# Conferir se o token continua vivo
python execution/verificar_token.py

# Gerar/renovar as credenciais
python execution/obter_token.py --token-curto "EAAG..."
```

## Requisitos

- Repositório **público** (necessário para a Meta baixar as artes).
  Não commite nada sensível — o `.env` já está no `.gitignore`.
- Conta Instagram Profissional vinculada a uma Página do Facebook.
- Python 3.9+ para rodar os scripts localmente.

## Migração segura

Rode o primeiro mês em paralelo: mantenha o agendamento no Meta Business Suite
e use `--dry-run` aqui. Quando os dry-runs passarem limpos por alguns dias,
desligue o agendamento manual.
