# Editar-video

`video_editado_3d.mp4`: versão editada do vídeo original.

- Pausas de respiração e trechos sem fala acima de 0,1s removidos (64,4s para 54,2s, 28 trechos de fala).
- Edição 3D feita em three.js: palco 3D com abertura voando, objetos metálicos com sombra na parede atrás da pessoa, esferas orbitando, partículas, zooms por corte e 7 transições 3D com whoosh.

Pipeline em `scripts/`: análise de áudio (Silero VAD + volume + vozeamento), segmentação, máscara da pessoa (MediaPipe selfie segmentation) e renderização 3D (`render.mjs` + `scene.html`).


## Testes de edição R7 (`r7_testes/`)

Seis formatos do mesmo roteiro (0 a 3 s, 3 a 5 s em vermelho, 5 a 7 s), sem nada na frente do rosto. Gerados por `scripts/r7_face.py` (rosto + máscara) e `scripts/r7_edit.py` (texto e animações). Cada frame é checado e o texto fica sempre abaixo do queixo.

### R7 tarjas com paleta nova (`scripts/r7_tarjas.py`)

Paleta: preto, branco, lima `#EAF56B`, roxo `#9D74FF`. `r7b_a_centralizado.mp4` mostra uma tela por vez, centralizada. `r7b_b_acumulado.mp4` empilha os textos sem sumir nenhum e deixa a chamada da legenda embaixo.

`r7c_agrupado_alto.mp4`: modelo centralizado mais alto (logo abaixo do queixo). O texto da tela 2 permanece e a chamada "LEIA A LEGENDA" entra embaixo dele aos 5 s.

`r7d_estilo_referencia.mp4`: mesmo agrupamento do r7c, no estilo de caixas retas do print de referência (fonte Poppins em `scripts/fonts/`, `scripts/r7_ref.py`).

`r7e_estilo_referencia_pb.mp4`: mesma legenda e tempos do r7d, com o vídeo em preto e branco (texto mantém as cores). A versão colorida r7d não foi alterada.
