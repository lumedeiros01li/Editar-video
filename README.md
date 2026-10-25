# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## video_modelos.mp4

Vídeo de teste (vertical 1080x1920, 74s). Legenda em caixa arredondada de uma linha, alinhada à fala (fixa em todos os trechos). Elemento do topo por trecho, com etiqueta no canto:

| Trecho | Elemento |
|---|---|
| Modelo 1 (escolhido) | Balão de resposta do Instagram |
| Modelo 2 (escolhido) | Texto de impacto, cor de destaque testada em amarelo, verde, ciano, laranja e rosa |
| Brutalista A | Cartão com borda preta grossa, sombra dura e cabeçalho mono rosa |
| Brutalista B | Fita listrada + barra preta mono + etiqueta verde-limão |
| Brutalista C | Bloco azul chapado com texto gigante e marca-texto verde-limão |

Scripts: `cortes_estilos.py` (cortes), `roteiro_estilos.json` (texto das legendas), `elementos_topo.py` (elementos em PNG) e `build_estilos.py` (alinha legenda à fala com whisper e monta tudo com ffmpeg).
