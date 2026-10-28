# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

`video_editado_gancho.mp4` (1080x1920, 42,4s): edição leve do vídeo "100 mil dólares".

- Respirações, pausas e a hesitação em "totalizando praticamente... cem mil" cortadas (55,7s para 42,4s).
- Gancho acima da cabeça enquanto o fundo é a parede: "QUASE US$ 100.000 POR ANO PARA SEU FILHO ESTUDAR NOS EUA", com o número em destaque lima. Some na troca para o extrato.
- Tratamento de imagem leve (redução de ruído, contraste, saturação e nitidez), aplicado antes da legenda.
- Legenda palavra por palavra (palavra atual em lima) no vídeo todo. Arquivo editável em `legenda.ass`.
- Pipeline em `scripts/corte_legenda/` (transcrição faster-whisper, corte por energia, geração do ASS, filtro ffmpeg).
