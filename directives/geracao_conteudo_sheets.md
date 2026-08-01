# Diretiva: Geração do Conteúdo do Mês

## Objetivo
Produzir de uma vez as meditações do mês inteiro, num formato que sirva
simultaneamente ao **Canva** (que monta as artes) e ao **publicador**
(que usa a legenda).

## Formato de saída

Uma planilha salva como `conteudo/AAAA-MM.xlsx` (ex.: `conteudo/2026-08.xlsx`)
com estas seis colunas, nesta ordem:

| Coluna | Conteúdo | Usada por |
|---|---|---|
| `dia` | Número do dia (1 a 31) | Publicador |
| `titulo` | Título curto, caixa alta, até 5 palavras | Canva |
| `texto_biblico` | **O texto do versículo** | Canva |
| `mensagem` | A reflexão, 3 a 5 linhas | Canva |
| `versiculo` | **A referência** (ex.: `Jó 8:7`) | Canva |
| `legenda` | O texto do post no Instagram | Publicador |

> Atenção à inversão: `texto_biblico` guarda o **texto** e `versiculo` guarda a
> **referência**. É assim que o template do Canva está mapeado.

### Por que `.xlsx` e não `.csv`

O Excel exporta CSV na codificação do sistema por padrão, o que **corrompe os
emojis** das legendas (`🌱` vira `ðŸŒ±`). Lendo o `.xlsx` direto, os emojis
chegam intactos e o passo de exportação some.

CSV continua funcionando, desde que salvo em **UTF-8**.

### Por que o nome do arquivo importa

Como a coluna é `dia` (1–31) e não a data completa, é o **nome do arquivo** que
diz de que mês se trata. Por isso `2026-09.xlsx`, nunca `setembro.xlsx`.

Se preferir, dá para usar uma coluna `data` com a data completa — aí o nome do
arquivo deixa de importar e você pode acumular vários meses num arquivo só.

---

## O prompt para a IA

```markdown
Atue como um Especialista em Marketing de Conteúdo Cristão e Devocionais.
Gere 30 dias de meditações diárias para o mês de SETEMBRO de 2026, no estilo
do site meditacaodiaria.com.br.

Entregue EXCLUSIVAMENTE uma tabela com estas 6 colunas, nesta ordem exata:

1. dia — o número do dia (1, 2, 3... até o último dia do mês)
2. titulo — título curto e chamativo, MAIÚSCULAS, máximo 5 palavras
3. texto_biblico — o TEXTO do versículo (a citação em si, não a referência)
4. mensagem — a reflexão, de 3 a 5 linhas, tom encorajador
5. versiculo — a REFERÊNCIA bíblica (ex: Jó 8:7)
6. legenda — o texto do post no Instagram

Regras:
- A legenda deve começar com um emoji, ter no máximo 400 caracteres, tom
  encorajador, e convidar a ler a meditação completa no link da bio.
- Não use aspas no início ou fim dos campos.
- Não inclua colunas extras nem texto antes ou depois da tabela.
- Varie os temas ao longo do mês; evite repetir livros bíblicos em dias seguidos.
```

Ajuste o mês e a quantidade de dias conforme o caso (28, 29, 30 ou 31).

---

## Como transformar em planilha

1. Copie a tabela gerada pela IA.
2. Cole no Excel ou no Google Sheets.
   - Se colar tudo numa coluna só: `Dados > Dividir texto em colunas`.
3. Confira que o cabeçalho ficou exatamente:
   `dia | titulo | texto_biblico | mensagem | versiculo | legenda`
4. Revise as legendas — é o único campo que vai ao ar sem passar pelo Canva.
5. Salve como `conteudo/AAAA-MM.xlsx` na pasta do projeto.

## Conferência

Depois de salvar, rode:

```bash
python execution/conferir_agenda.py --dias 30 --inicio 2026-09-01
```

Ele acusa linha faltando, legenda vazia e legenda acima de 2200 caracteres.
Nesta etapa as artes ainda não existem — é normal ele reclamar delas.

## Próximo passo
`directives/canva_bulk_create.md` — gerar as artes a partir desta mesma planilha.
