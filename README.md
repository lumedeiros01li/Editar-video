# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## video_estilos.mp4

Vídeo de teste de estilos (vertical 1080x1920, 67s). Pausas e respirações cortadas (97,4s para 67s), legenda embaixo e texto do assunto no topo. Cada seção usa um estilo diferente, identificado por uma etiqueta pequena no canto superior esquerdo:

| Seção | Tempo | Estilo |
|---|---|---|
| 1 | 0:00 a 0:14 | Clássico: legenda branca com contorno, título simples |
| 2 | 0:14 a 0:26 | Karaokê: palavra falada vira amarela, título em pílula azul, zoom alternado |
| 3 | 0:26 a 0:41 | Caixa: legenda em caixa cinza maiúscula, título em faixa, tom quente |
| 4 | 0:41 a 0:48 | Palavra: 1 a 2 palavras grandes com pop, título amarelo grande, zoom forte |
| 5 | 0:48 a 0:57 | Minimal: legenda fina, título serifado com linha, visual escurecido com vinheta |
| 6 | 0:57 a 1:07 | Gráfico: espectro do áudio animado no topo, legenda clássica |

Scripts: `cortes_estilos.py` (detecta fala e gera os cortes), `roteiro_estilos.json` (texto das legendas) e `build_estilos.py` (monta tudo com ffmpeg).
