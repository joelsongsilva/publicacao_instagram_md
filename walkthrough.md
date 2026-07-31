# Arquitetura — Automação de Publicações no Instagram

Registro das decisões técnicas do projeto "Meditação Diária".

## Camadas (conforme `agente.md`)

- `directives/` — os SOPs em Markdown (o que fazer)
- `execution/` — os scripts Python determinísticos (o trabalho em si)
- `.github/workflows/` — o agendador (quando fazer)
- `.tmp/` — intermediários descartáveis, fora do Git

## 1. Geração de conteúdo
Prompt de LLM produz a tabela do mês (Data, Titulo, Reflexao, TextoBiblico,
Versiculo, Legenda) → Google Sheets → exportado como CSV.
Ver `directives/geracao_conteudo_sheets.md`.

## 2. Geração das artes
Canva **Bulk Create** consome o mesmo CSV e gera 60+ páginas de uma vez.
Export em PNG → `execution/renomeador_imagens.py` renomeia `1.png, 2.png, ...`
para `YYYY-MM-DD_1.png` / `YYYY-MM-DD_2.png`, agrupando de dois em dois.
Ver `directives/canva_bulk_create.md`.

## 3. Publicação

O conteúdo (`conteudo/legendas.csv`) e as artes (`imagens/`) são commitados no
repositório. O GitHub Actions dispara `execution/publicar_carrossel.py` todo
dia às 05:00 BRT.

### Por que GitHub Actions e não n8n

A primeira versão deste projeto tentou n8n em Docker local. Foi descartada por
três motivos:

1. **Exigia máquina ligada às 05:00.** Um PC doméstico não serve como
   agendador; um VPS custaria mensalidade.
2. **O nó `instagramBusiness` não existe no n8n.** Instagram só via HTTP
   Request, nó do Facebook Graph, ou nós da comunidade.
3. **Erro conceitual no fluxo desenhado.** Ele baixava as imagens do Google
   Drive como binário e tentava enviá-las à API. A API de publicação do
   Instagram **não aceita upload de arquivo** — ela exige uma **URL pública**
   que a Meta baixa por HTTP. Isso invalidava o desenho inteiro.

O GitHub resolve os três de uma vez: é o cron, é a hospedagem pública das
imagens (`raw.githubusercontent.com`) e é gratuito.

### Fluxo da Graph API (v25.0)

```
POST /{ig-user-id}/media       image_url, is_carousel_item=true   → filho 1
POST /{ig-user-id}/media       image_url, is_carousel_item=true   → filho 2
GET  /{container-id}?fields=status_code                (polling até FINISHED)
POST /{ig-user-id}/media       media_type=CAROUSEL, children, caption → pai
GET  /{pai}?fields=status_code                         (polling até FINISHED)
POST /{ig-user-id}/media_publish  creation_id={pai}    → publicado
```

### Autenticação

**Page Access Token de longa duração**, que não tem data de expiração.
Obtido pela cadeia: token curto (1h) → token longo de usuário (60 dias) →
token de Página (perpétuo). Automatizado em `execution/obter_token.py`.

Como a publicação é só na conta própria, **não é necessária a Revisão de App
da Meta** — o app permanece em modo de desenvolvimento.

## 4. Rede de segurança

| Script | Papel |
|---|---|
| `publicar_carrossel.py --dry-run` | valida tudo sem publicar |
| `conferir_agenda.py` | avisa (semanalmente) se vai faltar material |
| `verificar_token.py` | avisa (semanalmente) se o token morreu |
| `logs/publicados.csv` | trava anti-duplicidade + auditoria |

Toda falha de workflow gera e-mail automático do GitHub.

## Resultado

O trabalho diário no Meta Business Suite foi eliminado. O trabalho mensal caiu
para: gerar conteúdo → Canva Bulk Create → renomear → `git push`.
