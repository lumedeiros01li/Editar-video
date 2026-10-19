# Direção de arte

Leia antes de escrever qualquer plano. Estas regras existem porque o vídeo é visto num celular, em movimento, com som desligado em boa parte das vezes, por alguém que decide em 2 segundos se continua.

## Um estilo por Reel

Todo plano tem `"estilo": "blueprint"` ou `"estilo": "brutalista"`. Nunca os dois no mesmo vídeo: misturar dilui os dois.

| O vídeo é sobre | Estilo |
|---|---|
| Conta, simulação, "quanto precisa", juros, crescimento no tempo | `blueprint` |
| Mito contra fato, lista, alerta, erro comum, lei ou regra | `brutalista` |

Sem `estilo` no plano, o `preparar_plano.py` escolhe pelos componentes e pela fala e diz o motivo numa NOTA. O Lucas pode forçar o outro. Na dúvida entre os dois, pergunte no roteiro visual (passo 4), não depois do render.

Antes do primeiro plano de cada estilo, abra a imagem de referência em `references/estilos/` (`blueprint.png` ou `brutalista.png`). Ela é o alvo visual. A folha de contato mostra a referência no primeiro quadro.

## Paleta única

| Token | Valor | Blueprint | Brutalista |
|---|---|---|---|
| Roxo profundo | `#170A2E` | Fundo dos painéis e do papel | Não usa |
| Roxo | `#9966FF` | Linhas do quadriculado, barras, eixos, borda do painel, etiqueta `//` | Bloco atrás da palavra-chave, sombra dura, barra comum |
| Limão | `#EBFF70` | Resultado da conta, traço de caneta, barra de destaque, chip do CTA | Caixa de resposta, sticker, texto do chip do CTA |
| Preto | `#000000` | Não usa | Borda, texto, fundo do chip do CTA, faixa da legenda |
| Branco | `#FFFFFF` | Texto | Fundo do cartão |

O lilás `#F1EBFF` e o cinza `#4A4A4A` antigos saíram. Sem logo, sem marca, sem nome de instituição na tela. Cinza claro `#EDEDED` só como trilho vazio de barra no Brutalista.

## Tipografia

Uma fonte de título e uma de interface por estilo:

| Estilo | Título | Interface |
|---|---|---|
| Blueprint | Barlow 300 (light), destaque em Barlow 600 | JetBrains Mono 500/700 |
| Brutalista | Archivo Black (sempre em caixa alta) | JetBrains Mono 500/700 |

A JetBrains Mono é a fonte de interface dos dois estilos: rótulos, contas, etiquetas, legendas e avisos. É ela que liga visualmente os dois estilos, como nas peças de referência.

Tamanhos mínimos em 1080 x 1920: 46 px para qualquer texto que a pessoa precisa ler. Exceções: etiqueta (40 px), aviso legal e fonte do dado (28 a 30 px). Se não cabe, corte palavras. O motor só encolhe sozinho o número grande e a palavra de impacto, e o `preparar_plano.py` avisa quando isso acontece.

## Blueprint

Sensação: caderno de engenharia. Preciso, calmo, nada sobra.

- **Painel:** quadro escuro `#170A2E` com quadriculado roxo de 30 px e borda fina roxa. É assim que número, lista, comparação, gráfico, conta e título ficam por cima do vídeo.
- **Título:** Barlow light branca. `**palavra**` vira Barlow semibold, sem cor nem sublinhado: o contraste de peso é o destaque.
- **Etiqueta:** `"etiqueta": "resolução"` vira `// resolução` em Mono roxo, como comentário de código, colado em cima do título ou do cartão.
- **Quadro de conta:** rótulo à esquerda e valor à direita, em Mono (`"rotulo": "× 12 meses", "valor": "120.000"`). Parênteses ficam apagados. Cada linha é escrita caractere por caractere no instante em que o Lucas fala aquele número. Antes do resultado, uma linha tracejada roxa se desenha. A linha do resultado é limão e ganha o traço de caneta limão embaixo do valor.
- **Destaque do resultado:** traço de caneta limão que sublinha (padrão) ou circula o resultado (`"caneta": "circula"`), no `numero`, na `conta` e no valor final do `grafico`.
- **Gráficos:** sobre papel milimetrado, eixos brancos que se desenham, linha branca, ponto final limão circulado.
- **Movimento:** painel se abre da esquerda como traço de régua (0,4 s), conteúdo sobe de dentro de máscara, traços se desenham. Sem mola, sem passar do ponto, nada quica.
- **Legenda:** texto branco em Barlow com contorno escuro duro, a palavra falada ganha sublinhado limão.
- **CTA:** caixa escura com borda roxa, texto em Barlow light, palavra em chip limão com texto preto.
- **Zoom:** suave por padrão.
- **Som:** clique de lápis em cada linha e item, risco de caneta quando o traço limão se desenha.

## Brutalista

Sensação: cartaz colado na parede. Seco, alto contraste, no tempo da batida.

- **Cartão:** branco, borda preta de 6 px, sem canto arredondado, sombra dura roxa de 14 px sem desfoque.
- **Destaque:** `**palavra**` ganha bloco roxo que varre por trás em 0,14 s, com texto branco (no fundo `roxo` o bloco é preto). A pontuação fica fora do bloco.
- **Resposta:** o número principal (`numero`, linha `resultado` da `conta`) fica numa caixa limão com borda preta e sombra roxa, com o rótulo em Mono caixa alta ("RESPOSTA =").
- **Etiqueta:** `"etiqueta": "pergunta"` vira `[ PERGUNTA ]` em Mono, texto simples colado em cima do elemento.
- **Elementos próprios:** carimbo MITO/FATO girado, sticker girado com frase curta, números em Archivo Black.
- **Quadro de conta:** linhas em Mono com rótulo à esquerda e valor à direita, régua preta grossa, resultado na caixa limão.
- **CTA:** cartão branco em Archivo Black, palavra em chip preto com texto limão.
- **Palavra de impacto:** bloco roxo com borda preta e texto branco.
- **Movimento:** cartão chega levantado e assenta na sombra em 0,1 s, com leve tremor de tela com semente. Saída é corte, não animação. Contagem de número em 6 degraus secos.
- **Legenda:** faixa preta, palavras brancas em JetBrains Mono, a palavra falada em limão.
- **Zoom:** seco por padrão (corte direto).
- **Som:** batida grave na entrada de cada cartão e de cada item.

## Zonas da tela

| Faixa (px) | Uso |
|---|---|
| 0 a 320 | Bloqueada: status do celular e nome do perfil |
| 330 a 700 | Título (gancho) |
| 700 a 1190 | Cartões, carimbo e palavra de impacto (o motor centraliza em 900 e nunca passa de 1190) |
| 1220 a 1370 | Legenda |
| 1270 a 1440 | CTA (a legenda some enquanto ele está na tela) |
| 1392 a 1440 | Aviso legal |
| 1450 a 1920 | Bloqueada: legenda do post, botões, comentários |
| 90 px de cada lado | Margem. Nada encosta na borda |

Rode a folha de contato com `--guias` para ver as faixas bloqueadas em vermelho.

## Padrões proibidos

- Misturar Blueprint e Brutalista no mesmo vídeo (o `preparar_plano.py` dá ERRO para carimbo e sticker no Blueprint).
- A seta dupla roxa (chevron) em qualquer forma, inclusive os caracteres » e >>. É elemento da marca InvestSmart.
- Brilho (glow) em qualquer elemento. No Blueprint a tentação de "neon" é grande: traço limão é chapado, sem halo.
- Título brutalista com mais de 8 palavras.
- Etiquetas soltas nos cantos da tela, molduras e bordas decorativas no quadro, barra de progresso. Etiqueta só colada ao elemento.
- Gradiente em qualquer elemento. Título centralizado em cima de gradiente.
- Tudo entrando com fade.
- Mola, quique ou passar do ponto no Blueprint. Transição suave no Brutalista.
- Canto arredondado e sombra com desfoque no Brutalista.
- Explosão genérica de partículas, confete, estrelinhas.
- Dois cartões ao mesmo tempo. Título dividindo a tela com cartão.
- Emoji decorativo sem relação com a frase. No Blueprint, emoji só se for essencial. No máximo 1 a cada 6 s.
- Texto que repete a legenda palavra por palavra em outro lugar da tela.

## Ritmo

- A cada 2 a 4 segundos algo novo acontece: cartão, item, zoom, palavra de impacto, troca de zoom no corte. A legenda não conta.
- Nada de 4 novidades no mesmo segundo. O olho precisa de 0,5 s para ler um cartão antes do próximo estímulo.
- Os primeiros 2 segundos têm título, palavra de impacto ou carimbo já no quadro 0.
- O elemento visual entra 2 quadros antes da palavra que ele ilustra (o `preparar_plano.py` faz isso sozinho).
- Zoom de corte: a cada corte de silêncio o enquadramento alterna entre 1,00 e 1,08. Isso esconde o pulo do jump cut nos dois estilos.

## Legenda

- Até 4 palavras e 24 caracteres por grupo. Quebra em pontuação e em pausa maior que 0,35 s.
- Números ditos por extenso viram algarismos: "mil e sessenta reais" vira "R$ 1.060". Junte as palavras na transcrição (veja `componentes.md`).
- Siglas sempre corretas: CDI, IPCA, Selic, FGC, LCI, LCA.
- Grafia revisada antes do primeiro render. Palavra errada na legenda é o erro mais visível do vídeo.

## Som

- Efeitos são sintetizados em código pelo `audio.py`, cada um no instante em que o elemento entra, com a paleta do estilo do plano.
- Efeitos ficam entre -15 e -33 dBFS de pico, bem abaixo da voz. Se o Lucas notar o efeito antes da fala, está alto: `"volume_sfx": -4`.
- Música só se o Lucas fornecer o arquivo. Ela entra a -30 dB e abaixa 9 dB sob a voz.
- Mix final em -14 LUFS, pico -1,5 dBTP.
