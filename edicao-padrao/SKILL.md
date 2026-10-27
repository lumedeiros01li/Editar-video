---
name: edicao-padrao
description: Edita vídeos verticais (Reels, Shorts, TikTok) no padrão definido. Corta pausas e respirações, remove takes errados e repetidos, aplica zoom, correção de cor, áudio normalizado, legenda em caixa arredondada alinhada à fala e um elemento no topo por trecho (balão de resposta do Instagram, frase de impacto ou painel brutalista). Use quando o usuário pedir para editar, legendar ou aplicar a edição padrão em um vídeo falado.
---

# Edição padrão

Entrada: vídeo falado em 9:16 (outras proporções são recortadas para preencher 1080x1920). Saída: MP4 1080x1920, 30 fps.

O que a edição faz em todo vídeo, sem configurar nada:

- **Cortes**: pausas, respirações e ruídos removidos. Só ficam trechos de fala, com fade de 12 ms em cada emenda para não estalar.
- **Takes**: erros de gravação e falas repetidas saem. Fica o último take completo de cada frase, ou o melhor.
- **Zoom**: alterna entre 100% e 108% a cada pausa longa na fala. Cortes colados dentro da mesma frase ficam no mesmo zoom. Mais um empurrão de 10% nos números ditos (automático, no mínimo 4 s entre eles).
- **Cor**: curva de contraste, tom levemente quente nas luzes e frio nas sombras, saturação +6%, redução de ruído, nitidez leve e vinheta suave. Só no vídeo, os elementos e a legenda não mudam de cor.
- **Áudio**: corte abaixo de 80 Hz, compressão leve e volume em -14 LUFS.
- **Legenda**: embaixo, em caixa escura arredondada, uma linha, até 24 caracteres, sincronizada palavra a palavra. Números e "mil" saem em lima.
- **Elemento no topo** por trecho, trocando conforme o assunto.

Pasta de trabalho: crie uma por vídeo (por exemplo `/tmp/edicao/<nome>`). Os scripts estão em `scripts/` ao lado deste arquivo. Use `-I` ao rodar Python em arquivos baixados.

## Passo a passo

1. **Preparar o ambiente** (uma vez): `sh scripts/preparar.sh`. Precisa de ffmpeg com libass, faster-whisper, Pillow e as fontes Inter, DejaVu e Noto Color Emoji.
2. **Cortes**: `python3 -I scripts/cortes.py <video> <dir>`. Gera `<dir>/keep.json` já sem pausas e sem respirações. Confira os números impressos. Se faltar fim de palavra ou sobrar pausa, ajuste `thr` e a histerese em `cortes.py`.
3. **Takes**: `python3 -I scripts/takes.py listar <video> <dir>`. Imprime cada trecho com tempo, nível em dB e texto. Escolha os trechos que formam a versão final de cada frase e rode `python3 -I scripts/takes.py manter <dir> 3-4,9,22-27`. O `keep.json` passa a ter só esses trechos (o completo fica em `keep_todos.json`).
   - Falas repetidas: use o último take completo, ou o melhor se o último tiver erro.
   - Descarte falsos começos ("Se o seu…", "Se você tem…"), apartes e hesitações. Um trecho que a transcrição devolve vazio e que está abaixo de -35 dB é respiração.
   - Nunca emende pedaços de takes diferentes no meio de uma frase se existir um take contínuo. A emenda muda a entonação. Quando precisar emendar, faça entre frases.
   - Confira o resultado: cada frase deve ter só uma tentativa, e o vídeo não pode mostrar quadros de takes descartados.
4. **Transcrição**: `python3 -I scripts/build.py transcrever <video> <dir>`. Lista as frases com o tempo já na linha do tempo cortada. Leva cerca de 1 minuto por 100 s de vídeo.
5. **Config**: crie `<dir>/config.json` a partir de `exemplo/config.json`.
   - `roteiro`: lista de frases com o texto corrigido do que foi dito. A transcrição erra nomes e termos técnicos, então corrija pelo contexto. Não invente fala que não existe e não inclua o que foi cortado. Se omitir `roteiro`, a legenda usa o texto bruto do Whisper.
   - `elementos`: lista em ordem. Cada um começa na frase `frase` (índice da lista `roteiro`) ou em `inicio` (segundos) e dura até o próximo. `fim` é opcional.
   - `cores`: `roxo` e `lima` (padrão `#9B6BFF` e `#E4FF6B`). Pode trocar por vídeo.
6. **Montar**: `python3 -I scripts/build.py montar <video> <dir> <dir>/config.json <saida.mp4>`. Leva cerca de 4 min para 50 s de vídeo.
7. **Conferir**: extraia quadros com `ffmpeg -ss <t> -i saida.mp4 -frames:v 1 q.png` em pelo menos um ponto de cada elemento. Veja se o elemento não cobre o rosto, se a legenda bate com a fala e se o início do vídeo não mostra falso começo.
8. **Entregar** o arquivo e avisar ao usuário quais trechos do texto ficaram incertos e quais takes foram descartados. Se o arquivo passar de 100 MB, recomprima com `-b:v 5M` antes de subir no GitHub.

## Elementos

| tipo | uso | transição | campos |
|---|---|---|---|
| `instagram` | Pergunta e resposta, contexto do tema. Cabeçalho escuro com a pergunta, corpo branco com a resposta. | não | `titulo`, `corpo` |
| `impacto` | Frase curta de gancho em cima. Branco com contorno preto e palavras-chave coloridas. | não | `linhas` (2 linhas, até uns 22 caracteres cada, palavras entre `*...*` ganham a cor), `cor` (`roxo`, `lima` ou hex) |
| `brutalista` | Números, comparações, conceitos. Painel cinza com margem, etiqueta `[ TAG ]`, título preto com bloco roxo e cartão branco com sombra roxa. | sim | `tag`, `preto`, `roxo`, `linhas` (cada uma `[rótulo, valor, etiqueta, riscado]`, no máximo 2). O valor aceita emoji, por exemplo `"📈"`. |

**Transição** é a entrada com fade e descida curta, mais o som "pop" (volume 0,45). Só o brutalista tem. `instagram` e `impacto` entram e saem secos, sem animação e sem som. Para mudar num elemento, use `"transicao": true` ou `false`.

Regras de uso:

- Alterne os modelos e as cores do destaque (roxo e lima). Troque o elemento a cada 6 a 12 segundos. Se o usuário pedir um modelo só, use só ele.
- Os textos dos elementos resumem o que está sendo dito naquele trecho. Use só dados que apareçam na fala.
- O brutalista com 2 linhas cobre cerca de um quarto do topo. Com o rosto alto no quadro, use 1 linha ou `y` negativo.

## Ajustes opcionais no config

| chave | efeito |
|---|---|
| `zoom` | zoom dos grupos alternados (padrão `1.08`, `1` desliga) |
| `zoom_gap` | pausa em segundos que troca o grupo de zoom (padrão `1.0`) |
| `zoom_enfase` | empurrão nos números (padrão `0.10`, `0` desliga) |
| `enfase` | lista manual `[{"frase": 1, "palavra": "60"}]` no lugar da automática. `[]` desliga |
| `destaque` | palavras coloridas na legenda: `{"lima": [...], "roxo": [...]}`. `destaque_numeros: false` desliga o automático |
| `grade` | filtro ffmpeg de cor no lugar do padrão. `false` desliga |
| `audio` | filtro ffmpeg de áudio no lugar do padrão. `false` desliga |
| `volume_pop` | volume do pop (padrão `0.45`, `0` desliga) |
| `legenda` | `max_caracteres`, `tamanho`, `centro_y` |

## Limites conhecidos

- Testado com vídeo de cerca de 50 s e 20 cortes, e antes com 100 s e 100 cortes. Com mais de uns 150 cortes o ffmpeg abre uma entrada por corte e pode faltar memória. Nesse caso, divida o vídeo em partes.
- O alinhamento da legenda usa o Whisper no áudio já cortado. Em trechos que ele reconhece mal, a legenda é interpolada e pode adiantar ou atrasar até cerca de meio segundo.
- A escolha dos takes depende da transcrição por trecho, que erra palavras. Trecho curto com texto estranho pode ser falso começo. Na dúvida, peça ao usuário para ouvir.
- Os elementos são desenhados para 1080x1920. Vídeos horizontais precisariam de outro layout.
- A correção de cor é calibrada para vídeo de celular em ambiente interno com luz baixa. Em vídeo já bem exposto, use `"grade": false` ou reduza a curva.
