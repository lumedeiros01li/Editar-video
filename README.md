# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## Edição leve (`video_editado_leve.mp4`)

55,3s para 29,6s. Cortes de respirações e pausas, erros de gravação removidos (início olhando pro lado, frase inicial repetida, tentativa errada do "Já aos 45", "Repara" repetido), legenda palavra a palavra, título no topo com destaque em R$ 10.000 de renda e cards de idade/valor na lateral direita, com o valor aparecendo quando é falado.

Pipeline: `scripts/leve_cortes.py` (pontos de corte), `scripts/leve_render.py` (legenda ASS + ffmpeg). Uso: `python3 scripts/leve_render.py original.mp4 saida.mp4`.

## Edição brutalista (`video_editado_brutalista.mp4`)

Mesmos cortes da edição leve, com:
- Zooms: punch-in alternando 1.00/1.13/1.04/1.17 a cada corte (reais e virtuais) com push lento, e pulso + tremida nas palavras-chave (60 anos, 10 mil, idades, valores, "dobra").
- Imagem: denoise, contraste, dessaturação leve, curva em S, sharpen, vinheta, grão e flash de 2 frames nos cortes.
- Som: denoise, EQ de voz, de-esser, compressor, whooshes nos cortes e hits de sub nas palavras-chave (sintetizados em `brutal_sfx.py`), -14 LUFS e pico abaixo de -1 dBFS.
- Visual brutalista: blocos amarelo/preto/branco com sombra dura, mono, cantoneiras e timecode, cards idade/valor, slams "QUASE 2X" e "MAIS DE 2X", legenda em caixa que vira amarela na palavra-chave.

Uso: `python3 scripts/brutal_render.py original.mp4 saida.mp4`.

## Edição simples (`video_editado_simples.mp4`)

Mesmos cortes, sem efeitos. Zoom leve (1.00/1.07) alternando só nos cortes, grade discreta, voz tratada (sem hits e whooshes). Visual de cartão claro com borda preta e sombra roxa: título "R$ 10.000 DE RENDA" num cartão no topo (o vídeo desce 210px e o topo ganha fundo desfocado), cards idade/valor e legenda em caixa clara, roxa na palavra-chave.

Uso: `python3 scripts/simples_render.py original.mp4 saida.mp4`.

## Edição padrão (`video_editado_padrao.mp4`)

Feita com a skill `scripts/edicao_padrao` (cortes de pausa, legenda em caixa de uma linha, elementos no topo trocando por trecho), mais: cartões idade/valor grandes na lateral esquerda (o valor entra quando é falado), topo desfocado para caber os elementos acima da cabeça e voz tratada. Config em `scripts/edicao_padrao/video_aposentadoria.json`, cortes em `video_aposentadoria_keep.json`.

Uso: `python3 -I scripts/edicao_padrao/scripts/build.py montar original.mp4 <dir com keep.json> scripts/edicao_padrao/video_aposentadoria.json saida.mp4`.

## Edição padrão, só brutalista (`video_editado_padrao_brutalista.mp4`)

Mesma edição padrão, com o modelo Brutalista C em todos os elementos do topo. Config em `scripts/edicao_padrao/video_aposentadoria_brutalista.json`.
