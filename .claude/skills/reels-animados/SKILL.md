---
name: reels-animados
description: Produz Reels 100% animados para o @lucasmedeiros.ai a partir de um roteiro e da voz gravada pelo Lucas. Escreve o roteiro com cenas, limpa o áudio (corta silêncios e respirações), transcreve, monta cenas animadas nas cores InvestSmart (frase cinética, número, ícones, personagem, moedas, gráfico, rosca, linha do tempo, lista, CTA) sincronizadas palavra por palavra, com legenda, trilha e efeitos sintetizados em código. Use SEMPRE que o pedido for "reels animado", "vídeo de animação", "explicar com animação", "contar uma história animada", "roteiro para eu gravar a voz", ou quando chegar um áudio de voz (m4a, wav, mp3) do Lucas para virar vídeo. Não use para editar vídeo em que o Lucas aparece (isso é edicao-grafica).
---

# Reels animados

Do tema ao vídeo pronto: roteiro, voz do Lucas, cenas animadas sincronizadas com a fala, legenda, trilha e mix em -14 LUFS.

Leia nesta ordem conforme a etapa:
- `references/roteiro.md` para escrever o roteiro e orientar a gravação.
- `references/direcao-de-arte.md` e `references/componentes.md` para montar as cenas.
- `references/qualidade.md` para o loop de revisão antes de qualquer entrega.

## Contrato de render

- Todo filme é uma função pura do tempo: `window.seek(t)` em `engine/engine.js` desenha o quadro do instante t.
- No motor: sem transição de CSS, sem setTimeout, sem requestAnimationFrame, sem estado carregado entre quadros. Ruído só com semente (mulberry32 no motor, `default_rng(crc32)` no áudio), nunca Math.random.
- Render com `node scripts/render.mjs`, H.264 yuv420p, CRF 16, 30 fps, 1080 x 1920.
- Trilha e efeitos sintetizados em código, a não ser que o Lucas forneça música. Acertos na grade de batidas (`beats.json`). Volume em -14 LUFS.
- Ao mexer no motor, mantenha o contrato: o mesmo quadro renderizado duas vezes sai idêntico.

## Pré-requisitos (primeira vez)

```bash
ffmpeg -version && python3 -c "import numpy, faster_whisper" && node -v
```
- ffmpeg: Mac `brew install ffmpeg`, Windows `winget install Gyan.FFmpeg`.
- `pip install numpy faster-whisper`.
- Node 18+: Mac `brew install node`, Windows `winget install OpenJS.NodeJS`.
- Na pasta `scripts` desta skill, uma vez: `npm install` e `npx playwright install chromium`.

No Windows troque `python3` por `python`. `<skill>` abaixo é a pasta desta skill.

## Fluxo

Trabalhe numa pasta por vídeo (ex.: `reels/2026-10-20-inflacao/`).

### Parte A. Roteiro (antes da gravação)

1. Siga `roteiro.md`: confirme tema, formato e CTA, confira dados com fonte, escreva o roteiro com cenas e o texto para gravar, rode o compliance e o humanizer.
2. Entregue os dois blocos e o guia de gravação. **Pare aqui** até o Lucas mandar o áudio.

### Parte B. Do áudio ao vídeo

3. **Limpar o áudio**
   ```bash
   python3 <skill>/scripts/cortar_silencios.py voz.m4a
   ```
   Sai `voz_cortado.m4a`. Mesmos parâmetros e ajustes da skill cortes-silencio.

4. **Transcrever e revisar**
   ```bash
   python3 <skill>/scripts/transcrever.py voz_cortado.m4a
   ```
   Leia `transcricao.txt` inteiro. Corrija grafia e siglas, junte números por extenso em algarismos, compare com o roteiro (frases repetidas e improvisos, ver `roteiro.md`).

5. **Plano de cenas.** Partindo do roteiro aprovado, escreva `plano.json` (`componentes.md`). Âncoras copiadas da transcrição real. Depois:
   ```bash
   python3 <skill>/scripts/preparar_plano.py plano.json
   ```
   ERRO impede o render. AVISO é regra quebrada: corrija ou justifique.

6. **Loop de qualidade** (`qualidade.md`): folha de contato com guias, tiras de movimento, nota em sete critérios, corrige os 3 piores, repete até tudo ser 8 ou mais.
   ```bash
   node <skill>/scripts/render.mjs plano_resolvido.json --folha --guias
   node <skill>/scripts/render.mjs plano_resolvido.json --movimento 3.1 --dur 0.6
   ```

7. **Áudio e render**
   ```bash
   python3 <skill>/scripts/audio.py plano_resolvido.json
   node <skill>/scripts/render.mjs plano_resolvido.json --final --audio audio_final.wav --saida reels_final.mp4
   ```
   Faça a conferência final de `qualidade.md`.

8. **Entrega**: caminho do vídeo, duração, as notas dos sete critérios e pendências de compliance (dado a confirmar, aviso padrão).

## Quando algo dá errado

- "Âncora não aparece na fala": o Lucas falou diferente. Copie o trecho exato de `transcricao.txt`.
- Elemento fora da área útil: o render avisa. Encurte o texto, reduza moedas ou itens, ou use `pos`.
- Tela vazia no começo da cena: a âncora da cena está cedo demais em relação ao primeiro elemento.
- Trilha alta ou baixa: `musica.volume` (padrão -28). Efeitos: `volume_sfx` em dB.
- Prévia rápida: `--rapido` no render final. A entrega é sempre sem `--rapido`.
