---
name: edicao-grafica
description: Edição completa de Reels falados do @lucasmedeiros.ai em um de dois estilos, Blueprint (papel quadriculado roxo profundo, Barlow light, quadro de conta em Mono, resultado e caneta em limão) ou Brutalista (Archivo Black, cartões com borda preta e sombra roxa, palavra-chave em bloco roxo, resposta em caixa limão, carimbo MITO/FATO), com legenda animada palavra por palavra, cartões de número, comparação, gráfico, lista, palavra de impacto, zoom nos cortes e efeitos sonoros sintetizados, sem logos. Roda depois da skill cortes-silencio. Use SEMPRE que o pedido for editar um vídeo de fala para Reels com legenda, elementos gráficos, motion, "deixar o vídeo profissional", "edição completa", "coloca legenda", "anima os números", ou quando um vídeo .mp4/.mov do Lucas falando chegar com pedido de edição que vá além de cortar silêncios.
---

# Edição gráfica de Reels

Pega um vídeo do Lucas falando e entrega o Reel editado: cortes de silêncio, legenda sincronizada, elementos gráficos ancorados na fala, efeitos sonoros e mix em -14 LUFS.

Cada Reel sai em **um** estilo: Blueprint para conta, simulação e "quanto precisa", Brutalista para mito contra fato, lista, alerta e lei. Nunca os dois no mesmo vídeo.

Leia antes de planejar: `references/direcao-de-arte.md` (estilos, paleta, zonas, movimento, proibições) e `references/componentes.md` (o que cada elemento faz e como escrever no plano). Abra a imagem do estilo em `references/estilos/`. O loop de revisão está em `references/qualidade.md`.

## Contrato de render

- Todo quadro é uma função pura do tempo: `window.seek(t)` em `engine/engine.js` desenha o quadro do instante t.
- No motor: sem transição de CSS, sem setTimeout, sem requestAnimationFrame, sem estado carregado de um quadro para o outro. Ruído só com semente (mulberry32 no motor, `default_rng(crc32)` no áudio), nunca Math.random.
- Render com `node scripts/render.mjs`, H.264 yuv420p, CRF 16, 30 fps, 1080 x 1920.
- Ao mexer no motor, mantenha o contrato. Um quadro renderizado duas vezes tem que sair idêntico.

## Pré-requisitos (checar na primeira vez)

```bash
ffmpeg -version && python3 -c "import numpy, faster_whisper" && node -v
```

Se faltar:
- ffmpeg e numpy: mesmos da skill cortes-silencio.
- `pip install faster-whisper` (o modelo baixa sozinho na primeira transcrição).
- Node 18 ou mais novo. Mac: `brew install node`. Windows: `winget install OpenJS.NodeJS`.
- Na pasta `scripts` desta skill, uma vez: `npm install` e `npx playwright install chromium`.

No Windows troque `python3` por `python`.

## Fluxo

Trabalhe numa pasta do vídeo (ex.: `reels/2026-10-17-poupanca/`). Todos os arquivos ficam lá. `<skill>` é a pasta desta skill.

### 1. Cortar silêncios
Rode a skill cortes-silencio no vídeo bruto. Saem `<nome>_cortado.mp4` e `<nome>_cortado_cortes.json`. Daqui em diante tudo usa o vídeo cortado.

### 2. Transcrever e revisar
```bash
python3 <skill>/scripts/transcrever.py <nome>_cortado.mp4
```
Leia `transcricao.txt` inteiro. Corrija grafia, siglas e nomes em `transcricao.json`, e junte números ditos por extenso em algarismos (como em `componentes.md`). Palavras marcadas "conferir" merecem atenção. Use `--modelo medium` se a transcrição vier com muitos erros.

### 3. Olhar o vídeo
Extraia 3 quadros (começo, meio, fim) e veja onde está o rosto e onde há área limpa:
```bash
ffmpeg -v error -ss 1 -i <nome>_cortado.mp4 -frames:v 1 -vf "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920" olhar_1.png
```
Defina `foco` (centro do rosto) e, se o rosto estiver baixo, ajuste `y` dos cartões ou `legenda.y`.

### 4. Roteiro visual e aprovação
Leia a fala e decida primeiro o estilo (tabela em `direcao-de-arte.md`), depois o que cada trecho pede: qual é o gancho, onde há número que merece cartão ou conta, onde há lista ou carimbo, qual é o conceito central, onde termina com CTA. Mostre ao Lucas um roteiro curto antes de construir, com o estilo na primeira linha e o motivo:

```
Estilo: blueprint (o vídeo é uma conta de aporte mensal)
0,0 s  título: "Seu dinheiro está parado?"
4,5 s  palavra: INFLAÇÃO
7,8 s  comparação: poupança x CDI (com aviso de exemplo)
11,4 s conta: renda 10.000 × 12 ÷ 0,06 → capital R$ 2.000.000
...
```
Espere a aprovação. Mudança aqui custa uma linha. Depois do render custa minutos.

### 5. Plano e verificação
Escreva `plano.json` seguindo `componentes.md`, com o `estilo` aprovado e sempre ancorando em índices de palavras. Depois:
```bash
python3 <skill>/scripts/preparar_plano.py plano.json
```
ERRO impede o render: corrija. AVISO é uma regra quebrada: corrija ou explique por que fica. O script gera `plano_resolvido.json`.

### 6. Loop de qualidade
Siga `references/qualidade.md`: folha de contato com guias, tiras de movimento, nota de 1 a 10 em seis critérios, corrige os 3 piores, repete até tudo ser 8 ou mais. Portão de compliance obrigatório.
```bash
node <skill>/scripts/render.mjs plano_resolvido.json --folha --guias
node <skill>/scripts/render.mjs plano_resolvido.json --movimento 7.7 --dur 0.6
```

### 7. Áudio e render final
```bash
python3 <skill>/scripts/audio.py plano_resolvido.json
node <skill>/scripts/render.mjs plano_resolvido.json --final --audio audio_final.wav --saida <nome>_final.mp4
```
Faça a conferência do render final descrita em `qualidade.md`.

### 8. Entrega
Em poucas linhas: caminho do arquivo, duração, estilo, elementos usados, as notas finais dos seis critérios e qualquer pendência de compliance (fonte de dado a confirmar, termo sensível na fala). A pasta `.quadros_30` pode ser apagada depois da entrega.

## Quando algo dá errado

- Cartão fora da área útil: o render avisa no terminal. Encurte o texto ou divida em dois cartões em momentos diferentes.
- Legenda cobrindo o cartão: o cartão está alto demais. Corte itens ou use `legenda.ocultar` naquele trecho.
- Emoji não aparece: falta fonte de emoji no sistema (Mac e Windows já têm).
- Render lento: `--rapido` gera uma prévia com encoder rápido. A versão final é sempre sem `--rapido`.
- Mudou só o plano: os quadros extraídos do vídeo ficam em cache, o próximo render pula essa etapa.
- "é do estilo X e o vídeo está em Y": o plano mistura componentes dos dois estilos. Troque o componente (carimbo vira palavra de impacto ou frase no Blueprint, sticker vira etiqueta) ou troque o estilo.
- Folha sem a referência: falta `references/estilos/blueprint.png` (imagem E da peça 1) ou `brutalista.png` (imagem C).
