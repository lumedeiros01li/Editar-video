# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).


## video_seguro_de_vida.mp4

Reel falado sobre seguro de vida e investimento (88,9s para 70,8s, 1080x1920).

- Respirações, pausas, 1 início falso, 1 virada de cabeça e a fala fora do roteiro cortados.
- Imagem: redução leve de ruído, contraste, saturação e nitidez, H.264.
- Caixa de pergunta estilo Instagram (cabeçalho escuro com a pergunta, corpo branco com a resposta), fixa durante todo o vídeo, acima da cabeça.
- Legenda por frase (Inter, branca sobre faixa escura translúcida), abaixo do queixo.

Gerado por `scripts/editar_reel.py ORIGINAL WORKDIR SAIDA scripts/reel_seguro_de_vida.json`.
