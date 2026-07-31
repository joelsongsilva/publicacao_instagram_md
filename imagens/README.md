# Artes do mês

As artes exportadas do Canva ficam aqui, **já renomeadas** pelo script
`execution/renomeador_imagens.py`.

## Regra de nomes (obrigatória)

```
YYYY-MM-DD_1.png   <- slide 1 (card da mensagem)
YYYY-MM-DD_2.png   <- slide 2 (card do link da bio)
```

Exemplo: `2026-08-01_1.png` e `2026-08-01_2.png`.

O script de publicação monta a URL a partir da data do dia. Se o nome estiver
diferente, o post falha com aviso de "arte não acessível publicamente".

## Importante

Estas imagens ficam **públicas** — é o que permite a Meta baixá-las na hora de
publicar. Isso não é um vazamento: elas seriam publicadas no Instagram de
qualquer forma. Mas **não coloque nada aqui que não deva ser público**.

## Limpeza

Depois que o mês passou, as artes podem ser apagadas do repositório para não
inchar o histórico. O `logs/publicados.csv` mantém o registro do que foi ao ar.
