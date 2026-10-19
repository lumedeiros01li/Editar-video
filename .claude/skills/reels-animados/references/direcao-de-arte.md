# Direção de arte das animações

## Um estilo por Reel

Todo plano tem `"estilo": "blueprint"` ou `"estilo": "brutalista"`. Nunca os dois no mesmo vídeo: misturar dilui os dois.

| O vídeo é sobre | Estilo |
|---|---|
| Conta, simulação, "quanto precisa", juros, linha do tempo de longo prazo | `blueprint` |
| Mito contra fato, lista, passo a passo, alerta, erro comum, lei ou regra | `brutalista` |

Sem `estilo` no plano, o `preparar_plano.py` escolhe pelos componentes e pela fala e diz o motivo numa NOTA. O Lucas pode forçar o outro. A decisão fica no roteiro (ver `roteiro.md`), antes da gravação.

Antes do primeiro plano de cada estilo, abra a imagem de referência em `references/estilos/` (`blueprint.png` ou `brutalista.png`). Ela é o alvo visual. A folha de contato mostra a referência no primeiro quadro.

## Paleta única

| Token | Valor | Blueprint | Brutalista |
|---|---|---|---|
| Roxo profundo | `#170A2E` | Papel de fundo de todas as cenas | Não usa |
| Roxo | `#9966FF` | Linhas do quadriculado, eixos, barras, etiqueta `//` | Fundo `roxo`, bloco atrás da palavra-chave, sombra dura, barra comum |
| Limão | `#EBFF70` | Resultado da conta, traço de caneta, chip do CTA | Caixa de resposta, sticker, moedas, texto do chip do CTA |
| Preto | `#000000` | Não usa | Fundo `preto`, borda, texto, régua da conta, chip do CTA, faixa da legenda |
| Branco | `#FFFFFF` | Texto e linha do gráfico | Fundo do cartão, carimbo |

Cinza claro `#F2F2F2` só como fundo `cinza` do Brutalista (`#EDEDED` no trilho vazio de barra). Sem logo, sem marca, sem nome de instituição.

## Fundos de cena

| Estilo | Fundos | Regra |
|---|---|---|
| Blueprint | `papel` (padrão e único) | O mesmo papel quadriculado o vídeo todo. As linhas se desenham no primeiro segundo. A variação vem dos elementos e das transições |
| Brutalista | `cinza` (padrão), `preto`, `roxo` | Alterne. Nunca 4 cenas seguidas no mesmo fundo. Texto preto no cinza e no roxo, branco no preto |

## Tipografia

| Estilo | Título | Interface |
|---|---|---|
| Blueprint | Barlow 300 (light), destaque em Barlow 600 | JetBrains Mono 500/700 |
| Brutalista | Archivo Black (sempre em caixa alta) | JetBrains Mono 500/700 |

A JetBrains Mono é a fonte de interface dos dois estilos: rótulos, contas, etiquetas, legendas e avisos. É ela que liga visualmente os dois estilos, como nas peças de referência. A legenda do Blueprint usa Barlow, porque é a fala e precisa de leitura rápida.

Mínimo de 46 px para texto de leitura. Etiqueta 40 px. Aviso e fonte 30 px. O motor só encolhe sozinho o número grande.

## Blueprint

Sensação: caderno de engenharia. Preciso, calmo, nada sobra.

- **Papel:** `#170A2E` com quadriculado roxo de 67,5 px bem apagado e linha forte a cada 270 px, como na referência. Os traços se desenham de cima para baixo e da esquerda para a direita no começo do Reel.
- **Título:** Barlow light branca. `**palavra**` vira Barlow semibold, sem cor nem sublinhado: o contraste de peso é o destaque.
- **Etiqueta:** `"etiqueta": "resolução, passo a passo"` vira `// resolução, passo a passo` em Mono roxo, como comentário de código.
- **Quadro de conta** (`conta`): caixa com borda roxa fina, rótulo à esquerda e valor à direita em Mono. Parênteses ficam apagados ("÷ taxa (6% a.a.)"). Cada linha é escrita caractere por caractere no instante em que o Lucas fala aquele número. Antes do resultado, uma linha tracejada se desenha. A linha do resultado é limão.
- **Destaque do resultado:** traço de caneta limão que sublinha (padrão) ou circula o resultado (`"caneta": "circula"`), no `numero`, na `conta` e no valor final do `grafico`.
- **CTA:** texto em Barlow light sem caixa, palavra em chip limão com texto preto.
- **Gráficos:** sobre papel milimetrado próprio, eixos brancos que se desenham, linha branca, ponto final limão.
- **Movimento:** traços que se desenham, conteúdo que sobe de dentro de máscara, ícone que abre em círculo. Nada quica, nada passa do ponto. A cena se aproxima 2,5% ao longo do tempo (respiração de câmera).
- **Legenda:** Barlow branca, a palavra falada ganha sublinhado limão.
- **Transições:** `corte`, `cortina` (com régua roxa na emenda), `lateral`, `empurra`.
- **Som:** trilha `suave`, clique de lápis em cada linha e item, risco de caneta quando o traço limão se desenha.

## Brutalista

Sensação: cartaz colado na parede. Seco, alto contraste, no tempo da batida.

- **Cartões:** comparação, gráfico, moedas, lista, linha do tempo e rosca ficam em cartão branco com borda preta de 6 px, sem canto arredondado, sombra dura de 14 px (roxa no cinza e no preto, preta no roxo). A frase cinética, a conta e o CTA ficam direto no fundo.
- **Entrada:** de uma vez. O cartão chega levantado e assenta na sombra em 3 quadros, com leve tremor de tela com semente (6 quadros). Saída é corte.
- **Destaque:** bloco roxo que varre por trás da palavra-chave em 0,14 s, com texto branco (no fundo `roxo` o bloco é preto). A pontuação fica fora do bloco.
- **Resposta:** o número principal (`numero`, linha `resultado` da `conta`) fica numa caixa limão com borda preta e sombra roxa, com o rótulo em Mono caixa alta ("RESPOSTA =").
- **Elementos próprios:** `carimbo` MITO/FATO girado, `sticker` girado, números em Archivo Black, contagem em 6 degraus.
- **Quadro de conta:** linhas em Mono com rótulo à esquerda e valor à direita, régua preta grossa, resultado na caixa limão.
- **CTA:** Archivo Black em caixa alta, palavra em chip preto com texto limão.
- **Etiqueta:** `"etiqueta": "pergunta"` vira `[ PERGUNTA ]` em Mono, texto simples colado em cima do elemento.
- **Legenda:** faixa preta, palavras brancas em JetBrains Mono, a palavra falada em limão.
- **Transições:** `corte` e `bloco` (a cena nova varre da direita em 0,12 s). A troca de fundo faz o papel que as transições suaves fazem no Blueprint.
- **Som:** trilha `pulso`, batida grave na entrada de cada cartão, item e troca de cena.

## Zonas

| Faixa (px) | Uso |
|---|---|
| 0 a 320 | Bloqueada (status e perfil) |
| 360 em diante | `pos: "alto"` |
| centro em 800 | `pos: "centro"` (padrão) |
| base em 1190 | `pos: "baixo"` |
| 1220 a 1370 | Legenda |
| 1250 a 1440 | CTA (a legenda some com ele) |
| 1392 | Aviso legal |
| 1450 a 1920 | Bloqueada (legenda do post e botões) |

Dois elementos na mesma cena: um `alto` e um `baixo`, ou um `alto` e um `centro` pequeno. O sticker não conta nesse limite. O render avisa quando algo passa de 1190.

## Padrões proibidos

- Misturar os dois estilos (o `preparar_plano.py` dá ERRO para carimbo ou sticker no Blueprint e para fundo ou transição do outro estilo).
- A seta dupla roxa (chevron) em qualquer forma, inclusive os caracteres » e >>. É elemento da marca InvestSmart.
- Brilho (glow) em qualquer elemento. No Blueprint a tentação de "neon" é grande: traço limão é chapado, sem halo.
- Título brutalista (frase) com mais de 8 palavras.
- Etiquetas soltas nos cantos da tela, molduras, barras de progresso. Etiqueta só colada ao elemento.
- Gradiente. Título centralizado em cima de gradiente.
- Tudo entrando com fade.
- Mola, quique ou passar do ponto no Blueprint. Transição suave no Brutalista.
- Canto arredondado e sombra com desfoque no Brutalista.
- Explosão de partículas, confete, estrelinhas.
- Ícone ou personagem que não tem relação com a frase.
- Frase cinética que repete a fala inteira. Ela mostra a ideia em até 6 a 10 palavras (8 no Brutalista).

## Ritmo

- Algo novo a cada 2 a 4 segundos (cena, elemento, item). A legenda não conta.
- Cena entre 1,2 e 6 s. Cena com tela vazia no começo é erro de âncora.
- Primeira cena com elemento visível no quadro 0.

## Som

- Trilha composta em código (`audio.py`): progressão calma em lá menor, 96 bpm por padrão. O estilo do plano escolhe a trilha: `suave` (pad, baixo e arpejo) no Blueprint, `pulso` (com bumbo e chimbal) no Brutalista. `musica.estilo` força a outra.
- A trilha fica 14 a 16 dB abaixo da voz e abaixa mais 9 dB enquanto o Lucas fala.
- Inícios de cena e de elemento são arrastados para a semicolcheia mais próxima da trilha (no máximo 78 ms a 96 bpm). Todo acerto visual e sonoro cai na grade de batidas, gravada em `beats.json`.
- Mix final em -14 LUFS.
