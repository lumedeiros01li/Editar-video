---
name: reels-r7
description: Produz Reels de Instagram no formato R7 do @lucasmedeiros.ai. São 7 segundos em loop, com 4 balões de texto Brutalistas sobre um vídeo sem fala, a chamada "LEIA A LEGENDA 👇", trilha, capa e folha de contato. Use quando o usuário pedir "edita o <ID>", "edita todos", "Reel R7", ou mandar um vídeo de fundo com roteiro de balões no padrão R7. Detecta o rosto e calcula um layout que nunca cobre olhos e boca.
---

# Reels R7

O Reel R7 tem exatamente 7 s (210 quadros a 30 fps) e é feito para loop. Sobre um vídeo de fundo do Lucas, sem fala, entram 4 balões de texto, um por vez, e no fim a chamada para a legenda. A edição é Brutalista, de intensidade calma, sem nenhum efeito extra.

O pipeline inteiro está em `scripts/r7.py`. Ele lê o roteiro do ID direto do arquivo de prompt da semana, prepara o vídeo, detecta o rosto, calcula o layout, renderiza os balões com Playwright, compõe com ffmpeg, gera a trilha e exporta tudo.

## Regras que nunca se quebram

1. O texto dos roteiros é aprovado pelo compliance. Copie exatamente, com acentos, aspas tipográficas e pontuação. Não reescreva, não resuma, não acrescente frase. O script já lê o texto do prompt sem alterar nada. Não edite o roteiro.
2. O primeiro quadro já mostra o balão 1. Os 3 primeiros segundos nunca ficam sem texto.
3. Nada de logo, nome ou cor de XP ou InvestSmart. Nenhuma seta dupla (chevron).
4. Proibido: degradê, brilho, neon, sombra desfocada, canto arredondado, fade de opacidade, transição de dissolver, imagem de banco.
5. Os balões nunca cobrem olhos e boca.
6. Só crie os arquivos de saída listados. Arquivos de trabalho ficam na pasta temporária.
7. Pergunte antes de instalar qualquer coisa fora da lista de ferramentas e antes de apagar arquivo do usuário.

## Ferramentas

- ffmpeg e ffprobe
- Node.js e Playwright (Chromium). O script acha o Playwright local ou o global.
- Python 3 com `opencv-python`, `mediapipe` e Pillow
- Fontes locais em `assets/fonts/`: Archivo Black e JetBrains Mono 400/700, copiadas do @fontsource, licença OFL. Nunca carregue fonte da internet.
- Emoji 👇: Noto Color Emoji do sistema
- Modelo de rosto local: `assets/blaze_face_short_range.tflite`

Faça uma checagem rápida antes:

```bash
python3 -c "import cv2, mediapipe, PIL"; node -e "import('playwright').catch(()=>process.exit(1))" || npm root -g; fc-list | grep -i "Noto Color Emoji"
```

Se faltar `opencv-python` ou `mediapipe`, pode instalar com `pip install opencv-python mediapipe`, porque estão na lista. Qualquer outra coisa, pergunte antes.

O mediapipe precisa da `libEGL.so.1`. Se o sistema não tiver, o `r7.py` usa sozinho a libEGL que vem com o Chromium do Playwright, sem instalar nada.

## Pastas

- Entrada: `~/reels-r7/entrada/<ID>.mp4`, com o nome do ID, por exemplo `QUI22-8.mp4`. Se o usuário mandar o vídeo como anexo, copie para essa pasta com o nome do ID. Se já existir um vídeo com esse nome, mova o antigo para a pasta temporária em vez de apagar e avise.
- Música opcional: `~/reels-r7/musica/`. O script usa o primeiro mp3 ou wav em ordem alfabética.
- Saída: `~/reels-r7/saida/<ID>/`

## Como rodar

```bash
python3 <skill>/scripts/r7.py <ID> --roteiros <arquivo_do_prompt.md> [--inicio <segundos>] [--base ~/reels-r7]
```

- O roteiro de cada ID fica no prompt, em blocos `### <ID> · <título>` com as linhas `1.` a `4.`, `Aviso no balão N: ...` (opcional) e `Capa: ...`. Destaques vão entre `[[ ]]`. Se o prompt veio como texto colado, salve-o como `.md` na pasta temporária e passe esse caminho.
- "edita o QUI22-8": rode só esse ID.
- "edita todos": rode cada vídeo de `entrada/` cujo nome bate com um ID do prompt, um por vez.
- O script imprime um JSON com fontes, larguras, linhas, passos da regra do rosto aplicados, música, LUFS, contagem de quadros, alertas e o caminho da folha de conferência.

Códigos de saída:

| Código | Significado | O que fazer |
|---|---|---|
| 0 | ok | Siga para a conferência |
| 2 | Nenhum layout evita olhos e boca | Nada foi exportado. Mostre o `quadro_problema` ao usuário (verde: área segura, amarelo: zona do rosto, vermelho: olhos até a boca, rosa: pilha, preto: chamada) e explique com números. Veja "Quando o rosto bloqueia" |
| 3 | Vídeo curto | Falta mais de 1 s a partir do início pedido. Avise e não exporte |

## Especificação implementada

Esta é a referência para conferir o resultado e para ajustar as constantes no topo de `scripts/render.mjs` e `scripts/r7.py`, se o usuário pedir mudança no padrão.

### Linha do tempo

| Tempo | Quadro | Evento |
|---|---|---|
| 0,0 s | 0 | Balão 1 já na tela, sem animação |
| 1,2 s | 36 | Entra o balão 2 |
| 2,4 s | 72 | Entra o balão 3 |
| 3,6 s | 108 | Entra o balão 4 |
| 4,6 s | 138 | Entra a chamada |
| 7,0 s | 210 | Corte seco |

- Entrada em 6 quadros: o elemento sobe 40 px com ease-out cúbico e a sombra cresce de 0 até o valor final, como um carimbo. A opacidade não muda.
- Os balões se acumulam e nada some. O layout é calculado uma vez, com os 4 balões, e nada se mexe depois de entrar.
- Cada estado da animação é um PNG próprio. O quadro depende só do número do quadro (`overlay` com `enable`). Nada de setTimeout, requestAnimationFrame ou transição CSS.

### Visual

Cores: roxo `#9966FF`, limão `#EBFF70`, preto `#000000`, branco `#FFFFFF`.

| Elemento | Fundo | Texto | Sombra dura |
|---|---|---|---|
| Balão 1 (gancho) | branco | Archivo Black, caixa alta, 64 px, até 3 linhas, senão reduz até 54 | roxa, 10 px |
| Balões 2 e 3 | branco | JetBrains Mono 700, 40 px, entrelinha 1,25, até 2 linhas, senão reduz até 34 | preta, 8 px |
| Balão 4 (virada) | limão | igual aos balões 2 e 3 | preta, 8 px |
| Chamada | preto | "LEIA A LEGENDA 👇", Archivo Black 44 px, texto limão, padding 16 x 28 | roxa, 6 px |

Valem para todos os balões:
- Borda preta de 6 px e canto reto.
- Padding de 28 px na vertical e 36 px na horizontal.
- Largura máxima de 800 px, e a caixa acompanha a linha mais larga do texto.
- Espaço de 26 px entre balões.
- Destaque `[[ ]]`: bloco roxo atrás e texto branco. Nunca quebra de linha: se quebrar, a fonte daquele balão desce. Os colchetes não aparecem.
- Aviso: última linha dentro do balão indicado, em JetBrains Mono 400, 24 px.

O vídeo de fundo não leva filtro, nem escurecimento, nem mudança de cor.

### Área segura e posição padrão

Coordenadas no vídeo de 1080 x 1920.

- Área segura: x 50 a 893, y 258 a 1525. Fora dela ficam a interface do topo, os botões da direita e a legenda com o nome do perfil.
- **Centro horizontal dos balões e da chamada: x 520.** Fica mais perto do meio do vídeo do que o centro da área (472). Os balões podem passar um pouco das bordas laterais da área, mas, contando a sombra, nunca ficam abaixo de x 30 nem acima de x 930.
- Com 800 px de largura, o balão vai de x 120 a 920 e a sombra até 930.
- **Pilha centralizada na vertical** no espaço livre entre y 270 e 40 px acima da chamada.
- O balão 1 pode subir até y 228, ou seja, 30 px acima da área.
- Os balões 2 a 4 ficam com a sombra dentro de y 258 a 1525.
- **Chamada menor e mais baixa:** centro em y 1500. Ela pode passar da base da área até y 1560, contando a sombra. A distância mínima para o balão 4 é de 40 px.

### Regra do rosto

1. O script tira 28 quadros (um a cada 0,25 s) do trecho de 7 s e roda o mediapipe face detection em cada um.
2. Todas as caixas viram uma caixa única. A zona do rosto é essa caixa com 40 px de margem.
3. A faixa proibida vai do topo da caixa única até 85% da altura dela, com a margem lateral. Nenhum balão, nem a chamada, pode tocar essa faixa.
4. O layout vale para o vídeo inteiro e não acompanha o rosto.

Se a posição padrão tocar a faixa proibida, os passos abaixo são aplicados em ordem e de forma cumulativa. O script para no primeiro que resolve.

1. Deslocar a pilha na horizontal para o lado oposto ao rosto, dentro dos limites laterais.
2. Reduzir a largura máxima de 800 até 600 px.
3. Reduzir as fontes até o mínimo: balão 1 até 52 px, balões 2 a 4 até 32 px.
4. Mover a pilha na vertical, ficando o mais perto possível do centro.
5. Mover a chamada (centro entre y 1440 e 1510) e reduzir a fonte dela até 38 px.
6. Layout dividido, já aprovado pelo usuário: balão 1 acima do rosto e balões 2 a 4 empilhados abaixo, todos centralizados no mesmo x, e o grupo de baixo centralizado no espaço entre o rosto e a chamada. Nesse passo vale a combinação que não toca a margem do rosto. Se nenhuma evitar a margem, vale a que tem as maiores fontes.

Se ainda houver toque na faixa proibida, o script sai com código 2. Encostar só na margem da zona do rosto é permitido, e vira alerta no resumo.

### Capa

- Quadro de 0,5 s com o texto da `Capa:` num balão igual ao balão 1.
- Fonte de 120 px, descendo até 96 px se precisar. Centro em x 540.
- O balão cabe inteiro no recorte do grid (y 285 a 1635) e segue a regra do rosto. A ordem de tentativa é: centro da tela, abaixo do rosto, acima do rosto.

### Música

- Se houver arquivo na pasta de música, o script usa o primeiro, cortado em 7 s e sem fade no fim.
- Se não houver, sintetiza um pad de acordes a 84 BPM (Cmaj9, Am9, Fmaj9), sem batida e sem voz, com o primeiro acorde já cheio no quadro 0.
- A trilha é normalizada com loudnorm em duas passadas lineares, para -14 LUFS integrado e pico até -1 dBTP.

### Saída em `~/reels-r7/saida/<ID>/`

1. `<ID>.mp4`: H.264, yuv420p, CRF 16, AAC 192 kbps, `+faststart`, exatamente 210 quadros.
2. `<ID>_sem_audio.mp4`: igual ao anterior, sem trilha.
3. `<ID>_capa.png`: 1080 x 1920.
4. `<ID>_contato.jpg`: folha com os quadros de 0,0 s, 1,3 s, 2,5 s, 3,7 s, 4,7 s e 6,9 s, mais a capa, sem marcações.

A cópia com marcações (`<ID>_contato_conferencia.jpg`) fica só na pasta temporária, para conferência. Nunca vai para a saída.

## Conferência antes de mostrar

Abra a folha de conferência com a ferramenta de leitura de imagem. As marcações são: verde para a área segura, amarelo para a zona do rosto, vermelho para olhos até a boca e azul para o recorte do grid na capa. Confira:

- O balão 1 está presente em 0,0 s.
- Nenhum balão toca o vermelho.
- Os balões 2 a 4 estão inteiros dentro do verde, na vertical. O título e a chamada ficam dentro das tolerâncias.
- O texto bate letra por letra com o roteiro, com acentos e aspas.
- Cada destaque está inteiro numa linha.
- Os balões não mudam de lugar entre os quadros.
- As sombras duras estão visíveis e o emoji foi renderizado.
- A capa está dentro do azul.
- A chamada contrasta com o fundo. O chip é preto: sobre fundo muito escuro, como calça ou sofá preto, a borda some e só sobra o texto limão. Isso não é erro, mas vale avisar.

Dê nota de 1 a 10 para cada quadro da folha. Se algo ficar abaixo de 8, corrija e rode de novo, no máximo 3 rodadas. Corrigir aqui quer dizer ajustar parâmetro ou trecho, nunca o texto. Se ainda houver nota abaixo de 8, pare e mostre o problema.

Para checar a animação, extraia os quadros 35 a 43 do mp4. O balão 2 deve subir e a sombra crescer.

## Quando o rosto bloqueia (código 2)

Explique em números a partir do JSON: a faixa proibida, a altura mínima da pilha (`altura_pilha_minima`) e o espaço livre acima e abaixo do rosto. Depois sugira um enquadramento concreto.

O que costuma funcionar é o rosto no terço de cima do quadro, com o topo do cabelo perto de y 130 a 260. Para isso, basta inclinar o celular um pouco para baixo ou se afastar. Assim sobram pelo menos 750 px abaixo da boca para a pilha.

Se o vídeo for mais longo que 7 s, teste outros inícios com `--inicio`.

## Resposta final

Responda só com:
- o ID
- a fonte e a largura de cada balão
- a fonte da chamada
- os passos da regra do rosto aplicados (ou "nenhum")
- se a música veio da pasta ou foi sintetizada
- os alertas: vídeo horizontal, quadro congelado, sobreposição na margem do rosto, contraste da chamada

Envie ao usuário o mp4, a folha de contato e a capa.
