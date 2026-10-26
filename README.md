# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## `video_brutalista.mp4` (Vox colagem + Brutalista)

Reedição completa do vídeo do Morning Call de 26/10 (1080x1920, 62,3s), com a narração e a música originais.

- Legendas palavra por palavra (transcrição com faster-whisper), em blocos pretos com a palavra falada em amarelo.
- Fotos e recortes do vídeo original em retícula (halftone), papel rasgado, fita adesiva, carimbos, círculos e setas de caneta vermelha, letras de jornal recortadas.
- Base brutalista: grade exposta, HUD com timecode, tipografia pesada (Archivo Black, Anton, Space Mono), blocos invertidos, transições de bloco e de folha rasgada.
- Mesma ordem de cenas e textos do original, com cada animação sincronizada ao tempo da palavra narrada.

Pipeline em `brutalista/`: `prep.py` (papel, halftone, recortes), `captions.py` (blocos de legenda), `scene.js` + `index.html` (cenas em canvas), `render.cjs` (render quadro a quadro com Playwright). Depois: `ffmpeg -framerate 30 -i quadros/%05d.jpg -i original.mp4 -map 0:v -map 1:a -c:v libx264 -crf 20 -pix_fmt yuv420p -c:a copy video_brutalista.mp4`.
