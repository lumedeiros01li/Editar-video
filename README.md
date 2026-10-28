# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).


## video_pergunta_legenda.mp4

Reel falado "custo de estudar nos EUA" (55,7s para 42,5s, 1080x1920).

- Respirações, silêncios e 2 hesitações cortados (`scripts/editar_reel.py`).
- Imagem: redução leve de ruído, contraste, saturação e nitidez, H.264 CRF 17.
- Caixa de pergunta estilo Instagram, fixa durante todo o vídeo, acima da cabeça.
- Legenda palavra a palavra (JetBrains Mono, palavra ativa em limão), logo abaixo da caixa.
