# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## `reel_instagram.mp4` (Reel vertical 1080x1920, 47,6s)

Edição dos dois vídeos gravados no carro (registro de água / organização patrimonial), em sequência.

- Cortes: pausas e respirações removidas, mais os erros "Aí um dia passa" e a primeira tentativa de "Assim você garante..." (66s para 47,6s).
- Transições em todos os cortes: zoom punch com flash leve, whip pan com motion blur nas mudanças de assunto e fade escuro no trecho dramático.
- Câmera: zoom alternado por corte, push-in lento, movimento de mão sutil e tremida em "pior momento".
- Animações: emojis 3D (Fluent, MIT) e rótulos sincronizados com as palavras, no espaço do teto do carro.
- Legenda palavra a palavra (Montserrat Black), palavra atual destacada em roxo.
- Áudio: redução de ruído (RNNoise), EQ de presença, de-esser, compressor, -14 LUFS. Trilha ambiente sintetizada (~20 dB abaixo da voz, com ducking) e efeitos sonoros leves sintetizados (pop, whoosh, ding, tick).

Pipeline em `scripts/reel/`: transcrição (Whisper turbo + Parakeet v3 via sherpa-onnx), `timeline.py` (cortes), `cues.py` (animações e SFX), `render.mjs` + `scene.html` (render Canvas no Chromium), `audio.py` (mix).
