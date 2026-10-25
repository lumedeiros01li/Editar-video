# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## video_teste_final.mp4

Teste final com os modelos escolhidos (vertical 1080x1920, 74s), alternando por trecho:

- Legenda em caixa arredondada, uma linha, alinhada à fala (fixa).
- Modelo 1: balão de resposta do Instagram.
- Modelo 2: texto de impacto, destaque roxo (#9B6BFF) ou lima (#E4FF6B).
- Modelo Brutalista C: painel cinza (#F0F0F0), etiqueta [ TAG ], título preto com bloco roxo, cartão branco com borda preta, sombra roxa e etiquetas lima.

Scripts: `cortes_estilos.py` (cortes), `roteiro_estilos.json` (texto das legendas), `elementos_topo.py` (elementos em PNG) e `build_estilos.py` (alinha legenda à fala com whisper e monta tudo com ffmpeg).
