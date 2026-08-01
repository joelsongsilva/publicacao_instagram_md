# Resumo Executivo — Publicação Automática no Instagram

> Documento de consulta rápida. Se você esqueceu como algo funciona, comece por aqui.
> **Pasta do projeto:** `C:\projetos\publicacao_instagram_md`

---

## 1. O que este sistema faz

Publica sozinho, **todo dia às 05:00 (horário de Brasília)**, um carrossel de 2 slides
com legenda no Instagram `@meditacaoeencorajamento`.

Você não precisa mais abrir o Meta Business Suite para agendar. O trabalho passou a ser
**mensal**: você prepara o mês inteiro de uma vez e o sistema distribui dia a dia.

**Custo:** R$ 0. GitHub Actions e a API de publicação do Instagram são gratuitos.

---

## 2. O fluxo completo

```
   VOCÊ FAZ, UMA VEZ POR MÊS                      O SISTEMA FAZ, TODO DIA
   ─────────────────────────                      ───────────────────────

   1. Gerar conteúdo com IA
      └─> planilha do mês
          (dia, titulo, mensagem,
           versiculo, legenda)
                 │
                 ▼
   2. Canva → Criar em lote
      └─> 32 páginas PNG
          (31 dias + card do link)
                 │
                 ▼
   3. renomeador_imagens.py
      └─> 2026-08-01.png ... 2026-08-31.png
          2026-08_link.png
                 │
                 ▼
   4. conferir_agenda.py
      └─> valida os 31 dias
                 │
                 ▼
   5. git add / commit / push  ─────────────►  GitHub (o "original" do projeto)
                                                       │
                                                       │  cron: 05:00 todo dia
                                                       ▼
                                              publicar_carrossel.py
                                                       │
                                                       ├─ lê a legenda do dia na planilha
                                                       ├─ monta as URLs das 2 artes
                                                       ├─ envia à API oficial da Meta
                                                       └─ registra em logs/publicados.csv
                                                       │
                                                       ▼
                                                 POST NO AR 🎉
```

**Ponto-chave:** o `git push` é a entrega. Enquanto o material não for enviado ao
GitHub, ele não existe para o sistema — mesmo estando na sua pasta local.

---

## 3. Rotina mensal (o único trabalho recorrente)

Faça no fim do mês anterior. Leva cerca de 30 minutos.

```bash
cd C:\projetos\publicacao_instagram_md
```

| # | Passo | Comando / ação |
|---|---|---|
| 1 | Gerar o conteúdo do mês | Prompt de IA — ver `directives/geracao_conteudo_sheets.md` |
| 2 | Salvar a planilha | Como `conteudo/2026-09.xlsx` — **o nome define o mês** |
| 3 | Gerar as artes | Canva Criar em lote — ver `directives/canva_bulk_create.md` |
| 4 | Renomear as artes | `python execution/renomeador_imagens.py --dir "C:\caminho\do\export" --mes 2026-09` |
| 5 | Conferir | `python execution/conferir_agenda.py --dias 30 --inicio 2026-09-01` |
| 6 | Entregar | `git add .` &nbsp;→&nbsp; `git commit -m "conteudo de setembro"` &nbsp;→&nbsp; `git push` |

Só avance do passo 5 para o 6 quando **todos os dias** aparecerem como `ok`.

---

## 4. Estrutura dos arquivos

```
conteudo/2026-08.xlsx        planilha do mês (colunas: dia, legenda)
imagens/2026-08-01.png       card do dia 1        ─┐
imagens/2026-08-02.png       card do dia 2         │ slide 1
        ...                                        │
imagens/2026-08-31.png       card do dia 31       ─┘
imagens/2026-08_link.png     card do link          ← slide 2, o MESMO todo dia

execution/                   os scripts
directives/                  os passo a passo detalhados
logs/publicados.csv          registro do que já foi ao ar
.env                         suas credenciais (NUNCA vai para o GitHub)
.github/workflows/           o agendador
```

**O card do link não é duplicado.** Um arquivo por mês serve os 31 dias — é o mesmo
gesto que você fazia no Business Suite ao anexar sempre o mesmo último card.

---

## 5. O que roda sozinho

| Quando | O quê | Se falhar |
|---|---|---|
| Todo dia, 05:00 | Publica o carrossel do dia | GitHub manda e-mail |
| Toda segunda, 09:00 | Confere o token e se há conteúdo para 7 dias | GitHub manda e-mail |

Você **não precisa acompanhar**. O sistema só te procura quando há problema.

> O post pode sair entre 05:00 e 05:20 — o agendador do GitHub atrasa em horários
> de pico. É normal e não indica falha.

---

## 6. Comandos úteis

```bash
cd C:\projetos\publicacao_instagram_md

# Validar tudo sem publicar (seguro, não posta nada)
python execution/publicar_carrossel.py --dry-run --data 2026-08-15

# Publicar um dia manualmente
python execution/publicar_carrossel.py --data 2026-08-15

# Republicar um dia que já consta como publicado
python execution/publicar_carrossel.py --data 2026-08-15 --forcar

# Ver se falta material
python execution/conferir_agenda.py --dias 31 --inicio 2026-09-01

# Conferir se o token continua vivo
python execution/verificar_token.py
```

Também dá para rodar tudo pelo site, sem terminal:
**Actions → Publicar carrossel do dia → Run workflow**.

---

## 7. Quando algo dá errado

| Sintoma | Causa provável | Solução |
|---|---|---|
| Post não saiu e chegou e-mail de falha | Ver o log em Actions | Ler a mensagem — os scripts dizem o que falta |
| `Nenhuma linha para 2026-09-05` | Planilha do mês não foi enviada | Repetir a rotina mensal |
| `arte nao acessivel publicamente` | Arquivo não commitado, nome errado, ou repositório virou privado | Conferir `imagens/` e o `git push` |
| `Variaveis de ambiente faltando` | Secret apagado ou alterado no GitHub | Recadastrar em Settings → Secrets |
| `token nao consegue mais acessar a conta` | Token invalidado (troca de senha do Facebook) | Refazer passos 3–5 de `directives/setup_meta_app.md` |
| Post saiu duplicado | Publicação manual + automática no mesmo dia | Apagar um no Instagram; a trava normalmente impede |

**Primeiro lugar para olhar sempre:**
https://github.com/joelsongsilva/publicacao_instagram_md/actions

---

## 8. Mini-glossário do GitHub

Para consulta, já que você usa pouco.

| Termo | O que é, na prática |
|---|---|
| **Repositório** | A pasta do projeto guardada na nuvem. É o "original". |
| **Clone** | Baixar o repositório para o computador. Cria a pasta local. |
| **Commit** | "Salvar uma versão" com um nome. Fica no histórico, dá para voltar atrás. |
| **Push** | Enviar seus commits para a nuvem. **É o que entrega o material ao sistema.** |
| **Pull** | Trazer da nuvem o que mudou lá (ex.: o `logs/publicados.csv` que o robô grava). |
| **Actions** | O robô do GitHub. É ele que roda o script às 05:00. |
| **Workflow** | Uma receita para o robô. Temos duas: publicar e verificar. |
| **Secret** | Uma senha guardada de forma cifrada. O valor nunca é exibido de novo — só o nome aparece na lista. |
| **Run workflow** | Botão para acionar o robô na hora, sem esperar o horário. |

**Regra prática:** se você mexeu em arquivos e não deu `git push`, o sistema não viu.

> Se o `git push` reclamar de conflito, geralmente é porque o robô gravou o
> `logs/publicados.csv` na nuvem. Rode `git pull` antes e tente de novo.

---

## 9. Limites e garantias

- **Limite da API:** 100 posts por 24h. Usamos 1. Sem risco.
- **Legenda:** até 2200 caracteres. O script barra antes de tentar publicar.
- **Token:** não expira. Só é invalidado se você trocar a senha do Facebook ou
  remover o app.
- **Repositório público:** necessário para a Meta baixar as artes. Nunca coloque
  nada sensível ali — o `.env` já está protegido.
- **Sem risco de bloqueio da conta:** usamos apenas a API oficial da Meta. Nada de
  robôs de navegador ou bibliotecas não-oficiais, que é o que causa banimento.

---

## 10. Histórico

- **01/08/2026** — Primeiro post publicado pelo sistema:
  https://www.instagram.com/p/DbfeUspkbrV/
- Substituiu o agendamento manual no Meta Business Suite, que era feito
  post a post, todo fim de mês.
