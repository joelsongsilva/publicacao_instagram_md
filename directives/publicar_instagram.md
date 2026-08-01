# Diretiva: Publicar no Instagram (rotina mensal)

## Objetivo
Deixar o mês inteiro publicando sozinho às 05:00, sem tocar no Meta Business
Suite.

## Como funciona
A API do Instagram **não agenda posts**. Quem faz o papel de agendador é o
GitHub Actions: todo dia às 05:00 (horário de Brasília) ele acorda, procura na
planilha do mês a linha do dia de hoje, pega as duas artes correspondentes e
publica o carrossel via API oficial.

Por isso o trabalho é **mensal**, não diário: basta deixar o material do mês
no repositório.

---

## Rotina mensal (fazer uma vez por mês)

> **Pasta do projeto:** `C:\projetos\publicacao_instagram_md`
>
> Mantenha o projeto **fora do OneDrive** — a sincronização concorrente na
> pasta `.git` pode corromper o repositório. O backup é o próprio GitHub.
>
> Para a visão geral do fluxo, veja [resumo_executivo.md](../resumo_executivo.md).

### 1. Gerar o conteúdo
Siga `directives/geracao_conteudo_sheets.md`.

### 2. Gerar as artes
Siga `directives/canva_bulk_create.md` — inclusive a etapa de renomear com
`execution/renomeador_imagens.py`.

### 3. Colocar tudo no repositório

**A planilha** vai para `conteudo/AAAA-MM.xlsx` (ex.: `conteudo/2026-08.xlsx`).

- `.xlsx` é o formato preferido: preserva emojis sem risco de codificação.
  `.csv` também funciona, desde que salvo em **UTF-8**.
- Precisa das colunas **`dia`** (1 a 31) e **`legenda`**. As demais
  (`titulo`, `mensagem`, `versiculo`...) podem ficar — são ignoradas aqui,
  pois só servem ao Canva.
- **O nome do arquivo define o mês.** Com a coluna `dia`, é ele que diz se
  o "dia 5" é agosto ou setembro. Por isso `2026-08.xlsx`, não `agosto.xlsx`.
- Alternativa: uma coluna `data` com a data completa. Aí o nome do arquivo
  deixa de importar e dá para acumular vários meses num arquivo só.

**As artes** vão para `imagens/`:

```
2026-08-01.png  ...  2026-08-31.png    o card de cada dia (slide 1)
2026-08_link.png                       o card do link (slide 2)
```

> **O card do link não precisa ser duplicado.** Um único arquivo por mês é
> reutilizado automaticamente nos 31 dias — é o mesmo gesto que você fazia no
> Business Suite ao anexar sempre o mesmo último card.
>
> Se algum dia precisar de um slide 2 diferente, basta criar
> `2026-08-15_2.png`: um arquivo específico do dia tem prioridade sobre o
> card do mês.

### 4. Conferir antes de subir

```bash
python execution/conferir_agenda.py --dias 31 --inicio 2026-08-01
```

Ele lista dia a dia o que está faltando (linha na planilha, legenda vazia,
arte ausente). Só suba quando estiver tudo `ok`.

### 5. Enviar para o GitHub

```bash
git add imagens conteudo
git commit -m "conteudo de agosto/2026"
git push
```

Pronto. Não há mais nada a fazer no mês.

### 6. Teste final (recomendado)

Na aba **Actions > Publicar carrossel do dia > Run workflow**, com
`dry_run = true`. Isso valida token, CSV e se as artes estão acessíveis
publicamente — sem publicar nada.

---

## Publicar/republicar manualmente
Actions > **Publicar carrossel do dia** > **Run workflow**:
- `data`: a data desejada (ex.: `2026-08-15`)
- `dry_run`: **false**
- `forcar`: `true` apenas se aquele dia já constar como publicado

Ou localmente: `python execution/publicar_carrossel.py --data 2026-08-15`

---

## Proteções embutidas

| Risco | Proteção |
|---|---|
| Publicar duas vezes no mesmo dia | Trava via `logs/publicados.csv`; só passa com `--forcar` |
| Arte faltando ou com nome errado | Script confere a URL antes de publicar e aborta |
| Legenda acima do limite | Aborta se passar de 2200 caracteres |
| Token morrer sem aviso | Workflow semanal `verificar-token.yml` manda e-mail |
| Ficar sem conteúdo no fim do mês | `conferir_agenda.py` roda semanal e avisa 7 dias antes |
| Falha silenciosa | Toda falha do Actions gera e-mail do GitHub |

---

## Edge cases

**O post não saiu às 05:00 em ponto**
Normal. O agendador do GitHub Actions pode atrasar de 5 a 20 minutos em
horários de pico. Se precisar de precisão ao minuto, aí sim seria necessário um
servidor dedicado.

**Erro "arte nao acessivel publicamente"**
Três causas, nesta ordem de probabilidade: (a) o arquivo não foi commitado;
(b) o nome está errado; (c) o repositório está privado — o
`raw.githubusercontent.com` só serve arquivos de repositório público.

**Erro "Nenhuma linha para a data X"**
O mês virou e o CSV não foi atualizado. Rode `conferir_agenda.py`.

**Falhou por instabilidade da Meta**
Rode o workflow manualmente com `dry_run=false`. A trava anti-duplicidade
protege caso o post na verdade tenha saído.

**NUNCA fazer**
Não use `instagrapi`, bots de navegador ou automação por login/senha. Isso é o
que faz conta ser bloqueada. Só a Graph API oficial.

## Limites da API (folgados para este uso)
- 100 posts por 24h; carrossel conta como 1. Você usa 1.
- Carrossel: 2 a 10 slides. Você usa 2.
- Legenda: 2200 caracteres.
