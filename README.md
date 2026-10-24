# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## Reel R$ 100 / US$ 100 em 2000

`reel_r100_reais_e_dolar.mp4`: 1080x1920, 30 fps, 32,5s. Parte 1 em R$ (0 a 16,5s), virada (16,5 a 18,5s), parte 2 em US$ (18,5 a 32,5s).

Fonte em `scripts/reel_r100/`: `reel.html` desenha cada frame em canvas a partir de `series_video_reais_e_dolar.csv`, `render.js` exporta os frames com Playwright e `audio.py` sintetiza a trilha (batida forte em 16,5s).

```
python3 -c "s=open('reel.html').read();open('index.html','w').write(s.replace('__CSV__',open('series_video_reais_e_dolar.csv').read().strip()))"
node render.js frames all && python3 audio.py
ffmpeg -framerate 30 -i frames/%05d.png -i audio.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -af "lowpass=f=15000,alimiter=limit=0.7:level=false" -c:a aac -b:a 192k -shortest reel.mp4
```
