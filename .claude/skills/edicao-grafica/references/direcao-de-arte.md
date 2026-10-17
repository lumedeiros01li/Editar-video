# Direção de arte

Leia antes de escrever qualquer plano. Estas regras existem porque o vídeo é visto num celular, em movimento, com som desligado em boa parte das vezes, por alguém que decide em 2 segundos se continua.

## Marca

| Token | Valor | Uso |
|---|---|---|
| Roxo | `#9966FF` | Única cor de destaque: palavra ativa da legenda, número, barra, check, chip do CTA |
| Roxo claro | `#F1EBFF` | Área do gráfico, caixa de check vazia |
| Preto | `#000000` | Texto em cartão branco, caixa do CTA |
| Cinza | `#4A4A4A` | Texto secundário, barra de referência na comparação |
| Branco | `#FFFFFF` | Cartões, título, legenda sobre vídeo |

Sem logo, sem marca, sem nome de instituição na tela. Sem cores dos pilares antigos (amarelo, dourado, turquesa). Se o briefing pedir outra cor de destaque, ela substitui o roxo em tudo, nunca soma.

## Tipografia

Duas famílias, papéis fixos:

- **Barlow 700**: títulos, palavra de impacto, números grandes, cabeçalho de cartão.
- **Inter 700/800**: legenda, itens, rótulos, CTA. Inter 500 só no aviso legal e na fonte do dado.

Tamanhos mínimos em 1080 x 1920: 46 px para qualquer texto que a pessoa precisa ler. Abaixo disso só aviso legal e fonte (30 px). Se não cabe, corte palavras, nunca diminua a fonte.

## Zonas da tela

| Faixa (px) | Uso |
|---|---|
| 0 a 320 | Bloqueada: status do celular e nome do perfil |
| 330 a 700 | Título (gancho) |
| 700 a 1190 | Cartões e palavra de impacto (o motor centraliza em 900 e nunca passa de 1190) |
| 1220 a 1370 | Legenda |
| 1270 a 1440 | CTA (a legenda some enquanto ele está na tela) |
| 1392 a 1440 | Aviso legal |
| 1450 a 1920 | Bloqueada: legenda do post, botões, comentários |
| 90 px de cada lado | Margem. Nada encosta na borda |

Rode a folha de contato com `--guias` para ver as faixas bloqueadas em vermelho.

## Movimento

O motor já implementa as entradas abaixo. O plano escolhe o componente, não a animação.

- Título: cortina da esquerda para a direita (0,34 s) com o texto deslizando atrás.
- Cartões: sobem 70 px com mola leve e se revelam de baixo para cima.
- Palavra de impacto: letras sobem uma a uma de dentro de uma máscara, barra roxa varre da esquerda.
- Itens de lista: cortina lateral e o check se desenha.
- Barras e gráfico: crescem com o valor contando junto.
- Emoji: mola com leve giro.
- Legenda: o grupo entra com um pulo curto, a palavra falada ganha a pílula roxa.
- Zoom de corte: a cada corte de silêncio o enquadramento alterna entre 1,00 e 1,08. Isso esconde o pulo do jump cut e cria ritmo sem nenhum elemento novo.
- Zoom suave: aproximação de 0,4 s para frases de virada ("olha a conta", "presta atenção").

Saídas são mais rápidas que entradas (0,2 s). Nada entra só com fade.

## Padrões proibidos

- Título centralizado em cima de gradiente.
- Tudo entrando com fade.
- Etiquetas nos cantos, molduras e bordas decorativas no quadro, barra de progresso.
- Brilho (glow) em qualquer elemento de interface.
- Explosão genérica de partículas, confete, estrelinhas.
- Dois cartões ao mesmo tempo. Título dividindo a tela com cartão.
- Emoji decorativo sem relação com a frase. No máximo 1 a cada 6 s.
- Texto que repete a legenda palavra por palavra em outro lugar da tela.

## Ritmo

- A cada 2 a 4 segundos algo novo acontece: cartão, item, zoom, palavra de impacto, troca de zoom no corte. A legenda não conta.
- Nada de 4 novidades no mesmo segundo. O olho precisa de 0,5 s para ler um cartão antes do próximo estímulo.
- Os primeiros 2 segundos têm título ou palavra de impacto já no quadro 0. É o gancho que segura o polegar.
- O elemento visual entra 2 quadros antes da palavra que ele ilustra (o `preparar_plano.py` faz isso sozinho). Entrar depois parece atrasado.

## Legenda

- Até 4 palavras e 24 caracteres por grupo. Quebra em pontuação e em pausa maior que 0,35 s.
- Números ditos por extenso viram algarismos: "mil e sessenta reais" vira "R$ 1.060". Junte as palavras na transcrição (veja `componentes.md`).
- Siglas sempre corretas: CDI, IPCA, Selic, FGC, LCI, LCA.
- Grafia revisada antes do primeiro render. Palavra errada na legenda é o erro mais visível do vídeo.

## Som

- Efeitos são sintetizados em código pelo `audio.py`, cada um no instante em que o elemento entra.
- Efeitos ficam entre -22 e -31 dBFS de pico, bem abaixo da voz. Se o Lucas notar o efeito antes da fala, está alto: `"volume_sfx": -4`.
- Música só se o Lucas fornecer o arquivo. Ela entra a -30 dB e abaixa 9 dB sob a voz.
- Mix final em -14 LUFS, pico -1,5 dBTP.
