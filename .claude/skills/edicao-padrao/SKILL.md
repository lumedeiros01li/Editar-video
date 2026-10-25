---
name: edicao-padrao
description: Edita vídeos verticais (Reels, Shorts, TikTok) no padrão definido. Corta pausas e respirações, coloca legenda em caixa arredondada de uma linha alinhada à fala e aplica elementos no topo (balão de resposta do Instagram, texto de impacto com destaque colorido, painel brutalista). Use quando o usuário pedir para editar, legendar ou aplicar a edição padrão em um vídeo falado.
---

# Edição padrão

Entrada: vídeo falado em 9:16 (outras proporções são recortadas para preencher 1080x1920). Saída: MP4 1080x1920, 30 fps, com:

- pausas e respirações acima de 0,1s removidas
- legenda embaixo, em caixa escura arredondada, uma linha, até 24 caracteres, sincronizada palavra a palavra com a fala
- um elemento no topo por trecho, trocando conforme o assunto

Pasta de trabalho: crie uma por vídeo (por exemplo `/tmp/edicao/<nome>`). Os scripts estão em `scripts/` ao lado deste arquivo. Use `-I` ao rodar Python em arquivos baixados.

## Passo a passo

1. **Preparar o ambiente** (uma vez): `sh scripts/preparar.sh`. Precisa de ffmpeg com libass, faster-whisper, Pillow e as fontes Inter e DejaVu.
2. **Cortes**: `python3 -I scripts/cortes.py <video> <dir>`. Gera `<dir>/keep.json`. Confira a duração final impressa. Se sobrar muita pausa ou palavras forem cortadas no fim, ajuste `thr` e a histerese em `cortes.py`.
3. **Transcrição**: `python3 -I scripts/build.py transcrever <video> <dir>`. Lista as frases com o tempo já na linha do tempo cortada. Leva cerca de 1 minuto por 100s de vídeo.
4. **Config**: crie `<dir>/config.json` a partir de `exemplo/config.json`.
   - `roteiro`: lista de frases com o texto corrigido do que foi dito. A transcrição erra nomes e termos técnicos, então corrija pelo contexto. Não invente fala que não existe e não inclua o que foi cortado. Se omitir `roteiro`, a legenda usa o texto bruto do Whisper.
   - `elementos`: lista em ordem. Cada um começa na frase `frase` (índice da lista `roteiro`) ou em `inicio` (segundos) e dura até o próximo. `fim` é opcional.
   - `cores`: `roxo` e `lima` (padrão `#9B6BFF` e `#E4FF6B`). Pode trocar por vídeo.
5. **Montar**: `python3 -I scripts/build.py montar <video> <dir> <dir>/config.json <saida.mp4>`. Leva cerca de 1,5 min para 75s de vídeo.
6. **Conferir**: extraia quadros com `ffmpeg -ss <t> -i saida.mp4 -frames:v 1 q.png` em pelo menos um ponto de cada elemento e olhe. Veja se o elemento não cobre o rosto e se a legenda bate com a fala.
7. **Entregar** o arquivo e avisar ao usuário quais trechos do texto ficaram incertos.

## Elementos

| tipo | uso | campos |
|---|---|---|
| `instagram` | Modelo 1. Pergunta e resposta, contexto do tema. Cabeçalho escuro com a pergunta, corpo branco com a resposta. | `titulo`, `corpo` |
| `impacto` | Modelo 2. Frase curta de gancho. Branco com contorno preto e palavras-chave coloridas. | `linhas` (2 linhas, até uns 22 caracteres cada, palavras entre `*...*` ganham a cor), `cor` (`roxo`, `lima` ou hex) |
| `brutalista` | Modelo Brutalista C. Números, comparações, conceitos. Painel cinza com margem, etiqueta `[ TAG ]`, título preto com bloco roxo e cartão branco com sombra roxa. | `tag`, `preto`, `roxo`, `linhas` (cada uma `[rótulo, valor, etiqueta, riscado]`, no máximo 2) |

Regras de uso:

- Alterne os modelos e as cores do destaque (roxo e lima). Troque o elemento a cada 6 a 12 segundos.
- Os textos dos elementos resumem o que está sendo dito naquele trecho. Use só dados que apareçam na fala.
- O brutalista com 2 linhas cobre cerca de um quarto do topo. Com o rosto alto no quadro, use 1 linha ou `y` negativo.
- Legenda: `legenda` no config aceita `max_caracteres`, `tamanho` e `centro_y`.

## Limites conhecidos

- Testado com vídeo de cerca de 100s e 60 cortes. Com mais de uns 150 cortes o ffmpeg abre uma entrada por corte e pode faltar memória. Nesse caso, divida o vídeo em partes.
- O alinhamento da legenda usa o Whisper no áudio já cortado. Em trechos que ele reconhece mal, a legenda é interpolada e pode adiantar ou atrasar até cerca de meio segundo.
- Os elementos são desenhados para 1080x1920. Vídeos horizontais precisariam de outro layout.
