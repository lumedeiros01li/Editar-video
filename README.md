# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).

## Skill `edicao-padrao`

Em `.claude/skills/edicao-padrao/`. Corta pausas, coloca legenda em caixa (uma linha, sincronizada com a fala) e aplica elementos no topo: balão do Instagram, texto de impacto e painel brutalista (cores roxo `#9B6BFF` e lima `#E4FF6B`). Veja `SKILL.md` para o passo a passo e `exemplo/config.json` para o formato.

`video_teste_final.mp4` é o resultado da skill sobre o vídeo de teste (vertical 1080x1920, 74s), gerado com `exemplo/config.json`.
