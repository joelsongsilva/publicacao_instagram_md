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

## Pré-requisito

Sua conta do Instagram precisa ser **Profissional (Comercial/Criador)** e estar
**vinculada a uma Página do Facebook**. Se você já agenda pelo Meta Business
Suite, isso já está feito — mas confirme em:
`Instagram > Configurações > Conta profissional > Compartilhamento com a Página`.

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

2. **Registre-se como desenvolvedor (primeira vez apenas).** Enquanto isso não
   for feito, o botão de criar app não existe. Clique em **Começar**
   (*Get Started*), aceite os termos, confirme e-mail/telefone e escolha a
   função **Desenvolvedor**. Leva ~2 minutos e é gratuito.

3. Vá em **Meus Apps** > **Criar aplicativo**
   (atalho: <https://developers.facebook.com/apps/creation/>).

4. Em caso de uso, escolha **Outro** e depois tipo de app **Empresa**
   (*Business*).

5. Nome: `Meditacao Diaria - Publicador`.
   **Quando perguntar se quer vincular a uma conta comercial, pule.** Vincular
   dispara exigência de verificação de empresa (envio de documentos, dias de
   espera) que é desnecessária para publicar na própria conta.

6. Criado o app, vá em **Adicionar produto** e adicione **Instagram**.

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
