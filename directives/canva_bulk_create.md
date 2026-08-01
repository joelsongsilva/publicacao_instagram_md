# Diretiva: Geração em Lote no Canva (Bulk Create)

## Objetivo
Transformar os dados gerados pela IA (que agora estão no Google Sheets) em 60 imagens/cards de forma quase instantânea utilizando a conta Canva PRO.

## Passos para o Canva Bulk Create

1. **Prepare os Dados**:
   - Vá no seu **Google Sheets** onde a IA gerou os dados do mês inteiro.
   - Baixe a planilha como **CSV** (Arquivo > Fazer download > Valores separados por vírgulas .csv). O Canva Bulk Create só aceita uploads de CSV, ou colagem manual no editor.

2. **Prepare o Design no Canva**:
   - Abra o seu template mensal com as **duas páginas (Card 1 Mensagem, Card 2 Link)**.
   - Certifique-se de que cada página tenha caixas de texto com tamanhos corretos para suportar o texto (sem quebrar ou sair das bordas).

3. **Inicie o "Criar em Lote"**:
   - No menu lateral esquerdo do Canva, vá em **Aplicativos** (Apps).
   - Busque por **Criar em lote** (Bulk create) e clique para abrir.
   - Clique em **Fazer upload de CSV** e selecione o arquivo que você baixou.
   *Alternativa*: Em vez do CSV, clique em *Inserir dados manualmente* e cole sua tabela da IA lá dentro.

4. **Conecte os Dados às Caixas de Texto**:
   - No seu design (Card 1), clique com o botão direito na caixa de texto do **Título**. No menu, vá em *Conectar dados* e escolha a coluna "Titulo".
   - Repita para **Reflexão**, **Versiculo** e **TextoBiblico**.
   - No Card 2 (ou se o link estiver no final da reflexão), use a mesma lógica. A coluna "Legenda" **não** deve ser conectada ao design: ela não aparece na arte, é usada só na hora da publicação (vai no texto do post).
   
5. **Gere as Imagens**:
   - Vai aparecer um botão roxo à esquerda **"Continuar"**. Clique nele.
   - Clique em **"Gerar X designs"** (sendo X os 30 ou 31 dias do mês do csv). Ele abrirá uma nova aba com todos os 60+ designs gerados (2 para cada dia do mês).
   - Revise visualmente para ver se nenhum versículo longo vazou da área segura. Ajuste pontualmente.

6. **Exporte e Renomeie**:
   - Clique em **Compartilhar -> Baixar**.
   - Escolha **PNG** e marque todas as páginas. O Canva vai baixar um arquivo `.zip`.
   - Extraia o `.zip` dentro da pasta `.tmp/imagens_canva` deste projeto.
   - O export tem **uma página por dia + a página final do card do link**
     (ex.: 32 páginas para um mês de 31 dias). O Canva nomeia como `1.png`,
     `2.png`, ..., `32.png`.
   - Rode o script, que renomeia e já move tudo para `imagens/`:
     ```bash
     python execution/renomeador_imagens.py --dir ".tmp/imagens_canva" --mes 2026-08
     ```
   - Resultado: `2026-08-01.png` ... `2026-08-31.png` e `2026-08_link.png`.
     O script confere sozinho se a quantidade de páginas bate com os dias do
     mês e avisa se algo saiu incompleto.

7. **Coloque a planilha e confira**:
   - Salve a planilha do mês como `conteudo/2026-08.xlsx` (o nome define o mês).
   - Rode a conferência antes de subir:
     ```bash
     python execution/conferir_agenda.py --dias 31 --inicio 2026-08-01
     ```
   - Estando tudo `ok`, siga para `directives/publicar_instagram.md` (passo 5).
