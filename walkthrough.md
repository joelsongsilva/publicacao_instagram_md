# Arquitetura — Automação de Publicações no Instagram

Registro das decisões técnicas do projeto "Meditação Diária".

## Camadas (conforme `agente.md`)

- `directives/` — os SOPs em Markdown (o que fazer)
- `execution/` — os scripts Python determinísticos (o trabalho em si)
- `.github/workflows/` — o agendador (quando fazer)
- `.tmp/` — intermediários descartáveis, fora do Git

## 1. Geração de conteúdo
Prompt de LLM produz a tabela do mês (Data, Titulo, Reflexao, TextoBiblico,
versiculo, legenda) salva como `conteudo/AAAA-MM.xlsx`.
Ver `directives/geracao_conteudo_sheets.md`.

**Por que `.xlsx` e não `.csv`:** o Excel exporta CSV na codificação do sistema
por padrão, corrompendo os emojis das legendas. Lendo o xlsx direto (openpyxl),
os emojis chegam intactos e o passo de exportação desaparece.

**Por que o nome do arquivo carrega o mês:** a planilha identifica as linhas por
`dia` (1–31), não por data completa. O mês vem do nome (`2026-08.xlsx`). Uma
coluna `data` completa também é aceita, e nesse caso o nome deixa de importar.

## 2. Geração das artes

Canva **Criar em lote** consome a mesma planilha. O export tem **uma página por
dia + uma página final** com o card do link — 32 páginas para um mês de 31 dias,
não 62.

`execution/renomeador_imagens.py` renomeia `1.png ... 31.png` para
`AAAA-MM-DD.png` e a última página para `AAAA-MM_link.png`, validando a
contagem contra os dias do mês.

**O card do link não é duplicado.** O publicador resolve o slide 2 nesta ordem:
`AAAA-MM-DD_2.png` (override do dia) → `AAAA-MM_link.png` (card do mês) →
`card_link.png` (fallback global). Um arquivo por mês serve os 31 dias, o que
evita ~17 MB de cópias idênticas no repositório a cada mês.

Ver `directives/canva_bulk_create.md`.

## 3. Publicação

O conteúdo (`conteudo/AAAA-MM.xlsx`) e as artes (`imagens/`) são commitados no
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

### Armadilhas encontradas no setup (registradas para não se repetirem)

Estão detalhadas em `directives/setup_meta_app.md`. Resumo do que custou tempo:

| Sintoma | Causa real |
|---|---|
| "Nenhum aplicativo encontrado" | Estava no Business Suite, não em `developers.facebook.com` |
| Botão de criar app inexistente | Faltava o registro prévio como desenvolvedor |
| Erro de "WorkPlatform" | Sessão de conta empresarial; o cadastro exige perfil pessoal |
| Perfil confundido com Página | A Central de Contas lista **perfis**, não Páginas. O teste válido é o menu "Selecionar perfil" |
| Produto Instagram "ausente" | Chama-se **"Graph API do Instagram"** e fica perto do fim da lista |
| `/me/accounts` vazio com tudo vinculado | A Página pertence a um **portfólio empresarial**, e nesse caso exige `business_management` além de `pages_show_list` |
| Publicação falhou às 05:00 | Os 4 secrets do GitHub haviam sido cadastrados como **um único secret** |

Duas dessas viraram código, não só documentação: o `obter_token.py` tenta
`/me/businesses → owned_pages` quando `/me/accounts` volta vazio, e diz
explicitamente que falta `business_management`.

### Outros defeitos corrigidos ao longo do caminho

- `os.getenv("X", default)` devolve `""` quando a variável existe porém vazia —
  não o default. Um `GRAPH_API_VERSION=` vazio no `.env` montava uma URL
  inválida. Trocado por `os.getenv("X") or default` nos três scripts.
- O console do Windows usa cp1252 e quebrava ao imprimir os emojis das
  legendas. A saída passou a ser forçada para UTF-8.

### Pontualidade do cron

O agendador do GitHub Actions nao garante horario: medimos atrasos de 51 min
(02/08) e 72 min (03/08) com `cron: "0 8 * * *"`. Hora cheia e o pior horario,
por ser o mais concorrido.

Solucao adotada, em duas camadas:

1. **Agendar cedo e esperar.** O cron principal roda as 04:07 BRT; o script
   valida tudo e so entao dorme ate as 05:00 (`--aguardar-ate`). O atraso do
   agendador e absorvido dentro dessa folga de 53 min. Se acordar depois das
   05:00, publica imediatamente.
2. **Horarios de reforco** as 04:37 e 05:07, com minutos quebrados para pegar
   fila menor. A trava anti-duplicidade impede post repetido.

A espera vem **depois** da validacao de conteudo e artes: se algo estiver
errado, o erro aparece imediatamente, e nao apos uma hora parado.

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
