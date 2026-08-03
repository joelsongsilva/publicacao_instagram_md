# Automação de Publicação no Instagram — Meditação Diária

Publica automaticamente, todo dia às 05:00 (horário de Brasília), um carrossel
de 2 slides com legenda no Instagram. Sem servidor, sem mensalidade, sem Meta
Business Suite.

> **📄 [Resumo Executivo](resumo_executivo.md)** — comece por aí se quiser
> relembrar o fluxo, a rotina mensal ou resolver um problema. Este README é a
> visão técnica.

**Status:** em produção desde 01/08/2026.
Primeiro post automático: https://www.instagram.com/p/DbfeUspkbrV/

## Como funciona

```
Conteúdo do mês (IA → planilha .xlsx)
        ↓
Canva Criar em lote  →  ZIP (31 dias + 1 card de link)
        ↓
renomeador_imagens.py  →  imagens/AAAA-MM-DD.png  +  imagens/AAAA-MM_link.png
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

A API do Instagram **não agenda posts**. Quem faz o papel de agendador é o cron
do GitHub Actions; o script publica no instante em que é chamado.

## Custo

Zero. GitHub Actions é gratuito e a API de publicação do Instagram também.

## Documentação

| Ordem | O quê | Onde |
|---|---|---|
| — | **Visão geral e consulta rápida** | [resumo_executivo.md](resumo_executivo.md) |
| 1 (uma vez) | Criar o app Meta e pegar o token | [directives/setup_meta_app.md](directives/setup_meta_app.md) |
| 2 (mensal) | Gerar o conteúdo do mês | [directives/geracao_conteudo_sheets.md](directives/geracao_conteudo_sheets.md) |
| 3 (mensal) | Gerar e renomear as artes | [directives/canva_bulk_create.md](directives/canva_bulk_create.md) |
| 4 (mensal) | Subir e conferir | [directives/publicar_instagram.md](directives/publicar_instagram.md) |
| — | Decisões de arquitetura | [walkthrough.md](walkthrough.md) |

## Estrutura

```
conteudo/2026-08.xlsx     conteúdo do mês (colunas: dia + legenda)
imagens/2026-08-01.png    card de cada dia (slide 1)
imagens/2026-08_link.png  card do link, o mesmo o mês inteiro (slide 2)
execution/                scripts Python
logs/publicados.csv       o que já foi ao ar (trava anti-duplicidade)
directives/               os passo a passo
.github/workflows/        o agendador
.env                      credenciais locais (fora do Git)
```

O card do link **não é duplicado**: um arquivo por mês serve os 31 dias.
Para um slide 2 diferente num dia específico, crie `AAAA-MM-DD_2.png` — ele
tem prioridade sobre o card do mês.

## Scripts

```bash
# Validar tudo sem publicar (seguro: não posta nada)
python execution/publicar_carrossel.py --dry-run --data 2026-08-15

# Publicar um dia específico
python execution/publicar_carrossel.py --data 2026-08-15

# Republicar um dia já registrado como publicado
python execution/publicar_carrossel.py --data 2026-08-15 --forcar

# Renomear as artes do Canva e mover para imagens/
python execution/renomeador_imagens.py --dir "C:\export" --mes 2026-09

# Ver se falta material
python execution/conferir_agenda.py --dias 31 --inicio 2026-08-01

# Conferir se o token continua vivo
python execution/verificar_token.py

# Gerar/renovar as credenciais
python execution/obter_token.py --token-curto "EAAG..."
```

## Automações ativas

| Workflow | Quando | O que faz |
|---|---|---|
| `publicar.yml` | Diário, 05:00 BRT | Publica o carrossel do dia (acorda 03:37 e aguarda a hora certa) |
| `verificar-token.yml` | Segundas, 09:00 BRT | Confere o token e se há conteúdo para 7 dias |

Ambos também podem ser acionados manualmente em **Actions → Run workflow**.

## Requisitos

- Repositório **público** (necessário para a Meta baixar as artes).
  Não commite nada sensível — o `.env` já está no `.gitignore`.
- Conta Instagram Profissional vinculada a uma Página do Facebook.
- Python 3.9+ para rodar os scripts localmente.
- Manter o projeto **fora do OneDrive**: a sincronização concorrente na pasta
  `.git` pode corromper o repositório. O backup é o próprio GitHub.

## Proteções embutidas

| Risco | Proteção |
|---|---|
| Publicar duas vezes no mesmo dia | Trava via `logs/publicados.csv`; só passa com `--forcar` |
| Arte faltando ou com nome errado | Checagem HTTP antes de chamar a API |
| Legenda acima do limite | Aborta se passar de 2200 caracteres |
| Token invalidado | Workflow semanal avisa por e-mail |
| Ficar sem conteúdo | `conferir_agenda.py` avisa com 7 dias de antecedência |
| Falha silenciosa | Toda falha do Actions gera e-mail do GitHub |
