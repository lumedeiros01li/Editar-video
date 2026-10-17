# Direção de arte das animações

## Marca

Quatro fundos de cena, cada um com um único destaque:

| Fundo | Texto | Destaque | Quando usar |
|---|---|---|---|
| `branco` | preto | roxo `#9966FF` | Cena padrão, explicação, listas |
| `lilas` | preto | roxo | Contas e dados, dá respiro sem perder a marca |
| `roxo` | branco | preto | Virada, conceito central, CTA |
| `preto` | branco | roxo | Tensão, problema, número que assusta |

Sem logo, sem marca, sem nome de instituição. Sem cores fora dessa tabela. Os círculos de fundo são o mesmo tom da cena, só um pouco mais claro ou escuro, e se movem devagar: dão vida sem disputar atenção.

## Tipografia

- **Barlow 700**: frases cinéticas, números, títulos de elemento, nomes de personagem.
- **Inter 700/800**: legenda, rótulos, itens, CTA. Inter 500 só em aviso e fonte.
- Mínimo de 46 px para texto de leitura. Aviso e fonte com 30 px.

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

Dois elementos na mesma cena: um `alto` e um `baixo`, ou um `alto` e um `centro` pequeno. O render avisa quando algo passa de 1190.

## Transições

| Transição | Sensação | Use em |
|---|---|---|
| `corte` | Seco, no tempo da música | Continuação do mesmo raciocínio, troca rápida |
| `cortina` | Nova camada sobe | Mudar de assunto dentro do vídeo |
| `circulo` | Abre a partir de um ponto (`origem: [x, y]`) | Revelar a resposta, zoom em um detalhe |
| `empurra` | Cena anterior sai por cima | Avançar no tempo, "e depois" |
| `lateral` | Cena anterior sai para a esquerda | Comparar: antes e depois, isso e aquilo |

Varie. A mesma transição três vezes seguidas vira vício. Toda troca de cena cai na grade da música.

## Movimento

O motor implementa. O plano só escolhe o componente.

- Palavras sobem de dentro de uma máscara, uma a uma, no instante em que são ditas (`sincronizar: true`).
- Números crescem com mola e contam até o valor.
- Ícones têm o traço desenhado e o disco entra com mola.
- Personagem sobe de baixo, respira (balança devagar), pisca em momentos com semente, e o balão abre com mola.
- Moedas caem e quicam, uma por vez.
- Barras, gráfico, rosca e linha do tempo crescem no instante da fala.
- O conteúdo de cada cena se aproxima 2,5% ao longo da cena (respiração de câmera).

## Padrões proibidos

- Título centralizado em cima de gradiente.
- Tudo entrando com fade.
- Etiquetas nos cantos, molduras, barras de progresso.
- Brilho (glow) em qualquer elemento.
- Explosão de partículas, confete, estrelinhas.
- Ícone ou personagem que não tem relação com a frase.
- Frase cinética que repete a fala inteira. Ela mostra a ideia em até 6 a 10 palavras. A legenda já carrega a fala.

## Ritmo

- Algo novo a cada 2 a 4 segundos (cena, elemento, item). A legenda não conta.
- Cena entre 1,2 e 6 s. Cena com tela vazia no começo é erro de âncora.
- Primeira cena com elemento no quadro 0.
- Fundos alternam: nunca 4 cenas seguidas no mesmo fundo.

## Som

- Trilha composta em código (`audio.py`): progressão calma em lá menor, 96 bpm por padrão. `estilo: "pulso"` tem bumbo e chimbal leves, `"suave"` só pad, baixo e arpejo.
- A trilha fica 14 a 16 dB abaixo da voz e abaixa mais 9 dB enquanto o Lucas fala.
- Efeitos sintetizados em cada entrada: whoosh nas transições, pop em números e ícones, clique nos itens, moedas tilintando, sino no CTA.
- Inícios de cena e de elemento são arrastados para a semicolcheia mais próxima da trilha (no máximo 78 ms a 96 bpm). Assim todo acerto visual e sonoro cai na grade de batidas, gravada em `beats.json`.
- Mix final em -14 LUFS.
