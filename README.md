# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## Edição leve (`video_editado_leve.mp4`)

55,3s para 29,6s. Cortes de respirações e pausas, erros de gravação removidos (início olhando pro lado, frase inicial repetida, tentativa errada do "Já aos 45", "Repara" repetido), legenda palavra a palavra, título no topo com destaque em R$ 10.000 de renda e cards de idade/valor na lateral direita, com o valor aparecendo quando é falado.

Pipeline: `scripts/leve_cortes.py` (pontos de corte), `scripts/leve_render.py` (legenda ASS + ffmpeg). Uso: `python3 scripts/leve_render.py original.mp4 saida.mp4`.
