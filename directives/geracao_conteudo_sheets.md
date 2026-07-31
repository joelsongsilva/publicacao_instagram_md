# Diretiva: Geração de Conteúdo Mensal (Google Sheets)

## Objetivo
Gerar o conteúdo de 30 dias para a Meditação Diária no Instagram, formatado de forma que possa ser copiado e colado diretamente no Google Sheets e consumido pelo *Bulk Create* do Canva.

## O Prompt para a IA (LLM)

Copie e cole o texto abaixo no ChatGPT/Claude para gerar o seu conteúdo do mês:

```markdown
Atue como um Especialista em Marketing de Conteúdo Cristão e Devocionais. 
Você vai gerar 30 dias de meditações diárias baseadas no site meditacaodiaria.com.br.

A saída deve ser EXCLUSIVAMENTE em formato de TABELA (Markdown ou CSV) contendo as seguintes 6 colunas, nesta exata ordem:

1. Data: (ex: 01/10/2023)
2. Titulo: (Um título chamativo e curto, máximo 5 palavras)
3. Reflexao: (Uma frase curta de reflexão, máximo 2 linhas)
4. TextoBiblico: (Referência bíblica, ex: João 3:16)
5. Versiculo: (O texto do versículo correspondente. Não use aspas no início ou fim para não quebrar a planilha)
6. Legenda: (Uma legenda pronta para o Instagram, incluindo 3 hashtags relevantes e a chamada para o link na bio apontando para meditacaodiaria.com.br. Quebre linhas usando \n se necessário ou mantenha um parágrafo único longo).

Regras de conteúdo:
- O tom deve ser encorajador, bíblico e focado em trazer o público para a meditação completa no site.
- Não insira colunas extras.
- Não coloque descrições antes ou depois da tabela. Entregue apenas a tabela preenchida com os 30 dias.
```

## Como Usar o Resultado (Google Sheets)
1. Quando a IA gerar a tabela, copie o conteúdo.
2. Abra sua planilha do Google Sheets chamada `Instagram Meditacao Diaria`.
3. Selecione a célula `A1` (logo abaixo do cabeçalho) e cole os dados copiados da IA.
4. Na sua planilha, em Google Sheets, selecione a coluna A e vá em Dados > Dividir texto em colunas. O conteúdo será dividido em colunas, da forma como é esperado.
5. Revise se alguma coluna ficou desalinhada por quebras de linha.

## Próximos Passos
- Esta planilha será conectada ao Canva (Criar em Lote).
- Cada coluna (`Titulo`, `Reflexao`, `Versiculo` etc) será mapeada para uma caixa de texto no seu design.
