# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## video_elementos.mp4

Vídeo de teste (vertical 1080x1920, 74s). Pausas e respirações cortadas, legenda em caixa arredondada de uma linha (até 24 caracteres) alinhada à fala, e um elemento diferente no topo a cada trecho (etiqueta "ELEMENTO n" no canto):

| # | Elemento |
|---|---|
| 1 | Balão de resposta do Instagram (cabeçalho escuro + corpo branco) |
| 2 | Texto de impacto, branco com palavras-chave amarelas |
| 3 | Serifado com destaque em itálico amarelo |
| 4 | Cartão de estatística (número grande + rótulo) |
| 5 | Balões de chat (recebido e enviado, entram em sequência) |
| 6 | Manchete com barra lateral amarela |
| 7 | Checklist animado |

Scripts: `cortes_estilos.py` (cortes), `roteiro_estilos.json` (texto das legendas), `elementos_topo.py` (elementos em PNG) e `build_estilos.py` (alinha legenda à fala com whisper e monta tudo com ffmpeg).
