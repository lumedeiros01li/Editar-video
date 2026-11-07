# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

`video_audio_melhorado.mp4`: vídeo do Drive com áudio tratado (`scripts/melhorar_audio.sh`).

- Redução de ruído com RNNoise (`arnndn`) + `afftdn`, corte de graves abaixo de 80 Hz.
- EQ para clareza da voz (-2 dB em 250 Hz, +3 dB em 3,5 kHz).
- Volume equilibrado entre falas: `dynaudnorm` + compressor. Variação de volume caiu de 12,4 LU para 6,0 LU.
- Loudness final -16 LUFS, pico -1,4 dBFS. Vídeo copiado sem recompressão.
