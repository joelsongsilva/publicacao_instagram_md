# Diretiva: Setup do App Meta (fazer UMA vez)

## Objetivo
Obter as duas credenciais que a automação precisa: `IG_USER_ID` e
`IG_ACCESS_TOKEN`. Tempo estimado: **30 a 45 minutos**. Depois disso, não se
mexe mais nisso.

## Por que NÃO precisa de App Review
A Revisão de App da Meta (que leva 2–4 semanas) só é exigida quando o app
publica em contas de **terceiros**. Como você vai publicar apenas na **sua
própria** conta, e você é administrador do app, o app fica permanentemente em
**modo de desenvolvimento** e funciona normalmente. Não submeta nada para
revisão.

---

## Passo 0 — Conferir o vínculo Página ↔ Instagram

Este é o pré-requisito que faz toda a automação funcionar. Sem ele, o
`obter_token.py` para com "nenhuma Página do Facebook encontrada".

A conta `meditacaoencorajamento` precisa ser **Profissional (Comercial ou
Criador)** e estar **vinculada a uma Página do Facebook**.

### Como saber se existe uma Página (verificação definitiva)

Não use a Central de Contas para isso: ela lista **perfis** (o que permite
login e cross-posting entre Facebook e Instagram) e **não** mostra o vínculo
Página ↔ Instagram que a API exige. Um perfil do Facebook com o nome da marca
não é uma Página.

O teste que não falha, no computador:

1. Logado em `facebook.com`, clique na **sua foto no canto superior direito**
2. O menu **"Selecionar perfil"** lista tudo que você gerencia

Se aparecer só o seu perfil e a opção **"Criar Página"**, não existe Página.

### Se não existir Página, crie uma (~2 min, grátis)

Ela funciona apenas como ponte técnica e pode ficar permanentemente vazia.

1. No menu acima, clique em **Criar Página**
2. Nome: `Meditação Diária`. Categoria: `Organização religiosa` (a categoria
   não afeta a API). Descrição é opcional.
3. **Pule** todas as telas seguintes de foto, capa, convites e anúncios
4. **Vincule ao Instagram** — este é o passo que importa:
   - Se o Facebook oferecer "Conectar o Instagram" logo após a criação, aceite
     e faça login na conta `@meditacaoencorajamento`
   - Se não oferecer: na Página, `Configurações > Contas vinculadas >
     Instagram > Conectar conta`
5. Confira: o menu "Selecionar perfil" agora deve listar **duas** entradas —
   o perfil e a Página

### Conta profissional

A conta do Instagram também precisa ser **Profissional** (Comercial ou
Criador). Confira em `Configurações e atividade > Para profissionais >
Tipo e ferramentas da conta` no app.

> Não perca tempo tentando validar o vínculo por menus além disso. O
> `obter_token.py` (passo 4) dá a resposta definitiva em 30 segundos e diz
> exatamente o que está faltando.

> **Não se preocupe se a Página não aparece no portfólio empresarial.**
> O Business Suite pode listar só o Instagram como ativo, e ainda assim a API
> funciona. O que importa é (a) o vínculo Página ↔ Instagram e (b) sua conta
> pessoal do Facebook ser **administradora** da Página.

---

## Passo 1 — Criar o app no Meta for Developers

> **Atenção ao site.** O portal de desenvolvedores é `developers.facebook.com`
> — fundo azul-escuro, menu com "Docs / Ferramentas / Suporte". Ele **não** é
> o Meta Business Suite (`business.facebook.com`), que tem menu lateral branco
> com "Configurações de publicidade" e "Todas as ferramentas".
> A seção *Apps* do Business Suite mostra apenas apps já vinculados à empresa e
> **não permite criar** nenhum — se você caiu numa tela dizendo "Nenhum
> aplicativo encontrado / Solicite acesso a um administrador", está no lugar
> errado.

1. Abra <https://developers.facebook.com/> **em uma aba nova**, sem navegar a
   partir do Business Suite. Confirme no canto superior direito que está logado
   na conta pessoal que administra a Página.

   > **Erro "you will be operating with your Facebook personal account, instead
   > of your current WorkPlatform one"?**
   > Seu navegador está numa sessão de conta empresarial (WorkPlatform), e o
   > cadastro de desenvolvedor só existe para contas pessoais. Clique em
   > **Acessar WWW** no aviso. Se não resolver, abra uma **janela anônima**,
   > faça login em `facebook.com` com a conta pessoal e só então volte para
   > `developers.facebook.com`.
   >
   > O registro de desenvolvedor é sempre de uma **pessoa**, nunca de um
   > portfólio empresarial. O portfólio é apenas um contêiner de ativos.

2. **Registre-se como desenvolvedor (primeira vez apenas).** Enquanto isso não
   for feito, o botão de criar app não existe. Clique em **Começar**
   (*Get Started*), aceite os termos, confirme e-mail/telefone e escolha a
   função **Desenvolvedor**. Leva ~2 minutos e é gratuito.

3. Vá em **Meus Apps** > **Criar aplicativo**
   (atalho: <https://developers.facebook.com/apps/creation/>).

4. Nome: `Meditacao Diaria - Publicador`.

5. O assistente pede **"Casos de uso"**. Nenhum dos destaques serve, e essa
   etapa **não é obrigatória** para o nosso objetivo — o que importa é o
   produto adicionado no passo 7. Se travar aqui, avance ou saia do assistente:
   o app é criado mesmo com "Tipo de aplicativo: Nenhum", e isso **não é
   problema**.

6. Se perguntar sobre portfólio empresarial, pode selecionar `Meditação Diária`
   ou pular — tanto faz. A verificação de empresa só é cobrada para acesso
   avançado, que não é o nosso caso.

7. **Este é o passo que realmente importa.** No **Painel** do app, procure a
   lista **"Produtos disponíveis"** e clique em **Configurar** na linha:

   > **Graph API do Instagram** — *Permita que empresas e criadores de conteúdo
   > publiquem e interajam com conteúdo, além de rastrear insights e hashtags.*

   Atenção: o item **não** se chama apenas "Instagram" e fica perto do fim da
   lista, entre "Pagamentos na web" e "Jobs". É fácil passar por cima dele.
   Não precisa preencher nada na tela que abrir — basta o produto ficar
   adicionado.

> **Criou o app em duplicidade?** Acontece, porque o assistente permite sair e
> recomeçar. Ter dois apps não quebra nada — o que quebra é misturar o App ID
> de um com o App Secret do outro. Identifique qual tem o Graph API do
> Instagram adicionado, e renomeie o outro para `ZZZ - NAO USAR`
> (`Configurações > Básico > Nome de exibição`) ou exclua-o no fim dessa mesma
> página.

> **Adicionou um produto errado sem querer** (ex.: Central de Apps)? Deixe como
> está. Produto não configurado não faz nada e não interfere em permissões,
> token nem publicação.

## Passo 2 — Guardar App ID e App Secret

Em **Configurações do app > Básico**, copie:
- **ID do aplicativo** → `META_APP_ID`
- **Chave secreta do aplicativo** (clique em "Mostrar") → `META_APP_SECRET`

Cole os dois no arquivo `.env` do projeto (copie de `.env.example`).

> Esses dois valores só são usados para gerar e conferir o token. Não são
> necessários para publicar.

## Passo 3 — Gerar o token curto

1. Abra o **Explorador da Graph API**:
   <https://developers.facebook.com/tools/explorer/>
2. No canto superior direito, em **Aplicativo Meta**, selecione o app que você
   acabou de criar.
3. Em **Usuário ou Página**, escolha **Token de acesso do usuário**.
4. Em **Permissões**, marque exatamente estas:
   - `instagram_basic`
   - `instagram_content_publish`
   - `pages_show_list`
   - `pages_read_engagement`
   - `business_management`
5. Clique em **Gerar token de acesso** e conclua o login/autorização. Autorize
   a Página e a conta do Instagram quando ele perguntar.
6. Copie o token gerado. **Ele vale só 1 hora** — siga direto para o passo 4.

## Passo 4 — Converter para o token definitivo

No terminal, na pasta do projeto:

```bash
pip install -r requirements.txt
python execution/obter_token.py --token-curto "COLE_O_TOKEN_AQUI"
```

O script faz a cadeia inteira: token curto → token longo de usuário → **token
de Página (que não expira)** → descobre o ID da conta Instagram. No fim ele
imprime:

```
IG_USER_ID=178414...
IG_ACCESS_TOKEN=EAAG...
```

Se ele imprimir `NAO expira (correto)`, está tudo certo.

Cole os dois valores no seu `.env` local.

## Passo 5 — Cadastrar os Secrets no GitHub

No repositório: **Settings > Secrets and variables > Actions >
New repository secret**. Crie quatro:

| Nome | Valor |
|---|---|
| `IG_USER_ID` | o ID impresso no passo 4 |
| `IG_ACCESS_TOKEN` | o token impresso no passo 4 |
| `META_APP_ID` | do passo 2 |
| `META_APP_SECRET` | do passo 2 |

## Passo 6 — Testar

```bash
python execution/verificar_token.py
```

Deve responder `OK - conectado a @seu_usuario` e
`OK - permissoes de publicacao presentes`.

---

## Edge cases

**"nenhuma Pagina do Facebook encontrada"**
A conta do Instagram não está vinculada a uma Página, ou você não marcou
`pages_show_list` no passo 3.

**"esta Pagina nao tem conta Instagram Business vinculada"**
A conta ainda é pessoal. Converta para Profissional no app do Instagram.

**O token aparece com data de expiração**
O passo 3 gerou um token de Página em vez de token de usuário. Refaça
escolhendo **Token de acesso do usuário**.

**`(#10) Application does not have permission for this action`**
Falta `instagram_content_publish`. Refaça o passo 3 marcando a permissão.

**A Meta mudou o layout dos menus**
Acontece com frequência. Os nomes dos produtos (`Instagram`) e das permissões
não mudam — procure por eles. Se travar, me mande o erro que o script devolveu.

## Quando será preciso repetir isso
Só se o token for invalidado, o que acontece em: troca de senha do Facebook,
remoção do app pelo usuário, ou revogação de permissões. O workflow
`verificar-token.yml` roda toda segunda e te avisa por e-mail se isso ocorrer.
Nesse caso, refaça apenas os passos 3, 4 e 5.
