# Reel animado: inflação em 7 países (@lucasmedeiros.ai)

MP4 de 26 s, 1080x1920, 30 fps, sem narração. Música e efeitos sintetizados em código. Estilo Brutalista, intensidade calma.

## Como rerodar

Requisitos: Node 22, ffmpeg, Playwright com Chromium (`npm i playwright`).

```
node render.mjs                # as duas versões: out/reel-inflacao-7-paises.mp4 (eixo linear) e ...-log.mp4
node render.mjs --eixo=log     # só a versão com eixo logarítmico
node verificar.mjs --eixo=log  # valores x dados.json, zona segura, colisões, sincronia, ffprobe, loudness
node contato.mjs --eixo=log    # folhas de contato em out/contact-sheets/<eixo>/
```

`node render.mjs --so-frames --frames=0,300,779` captura só quadros avulsos. As duas versões usam o mesmo áudio e a mesma linha do tempo, só muda o eixo Y. O áudio sai de `node audio.mjs`.

## Arquivos

| Arquivo | Função |
|---|---|
| `dados.json` | Séries, fonte, URL, data de coleta. Todo número do vídeo vem daqui |
| `modelo.mjs` | Interpolação, linha do tempo, tabela do eixo Y, marcos e ticks. Usado pelo vídeo e pelo áudio |
| `index.html` | Função de quadro `window.seek(t)` |
| `audio.mjs` | Trilha sintetizada, loudnorm em dois passos |
| `render.mjs`, `util.mjs` | Captura com Playwright e montagem com ffmpeg |
| `verificar.mjs`, `contato.mjs` | Verificações automáticas e folhas de contato |

## Fonte dos dados

- Indicador: Banco Mundial, FP.CPI.TOTL (índice de preços ao consumidor, média anual). A coluna do arquivo traz a inflação anual em %, e o índice foi encadeado a partir de 2000 = 100.
- Arquivo usado: `https://raw.githubusercontent.com/datasets/cpi/main/data/cpi.csv` (espelho secundário, pacote atualizado em 2025-06-05), coletado em 2026-10-23. SHA256 `182baa44c536079bea07bb8700c37c85441c3d7d5f8e6dd68fb92fcb4a7815e8`.
- Fonte primária a conferir: `https://api.worldbank.org/v2/country/{ISO3}/indicator/FP.CPI.TOTL.ZG?format=json&date=2000:2025&per_page=1000`. Não foi acessível do ambiente de build.

## Ressalvas

1. Espelho secundário do Banco Mundial, não fonte primária. Conferir antes de publicar.
2. Série anual. A linha usa interpolação monótona suave (PCHIP) entre anos, calculada no build. Valores entre dois anos são interpolados. Nos anos de dado, a tela bate com o `dados.json`.
3. O Reino Unido do Banco Mundial parece corresponder ao CPIH do ONS, e não ao CPI. Hipótese não confirmada. Mantido por consistência de metodologia.
4. Último ano disponível: 2024.
5. Rótulos do eixo X a cada 10 anos, com marcas a cada 5, para manter 40 px de texto sem rótulos colados.
6. O cartão do gráfico desce até y=1370 e a linha de fonte e o CTA ficam entre 1384 e 1450, no limite da zona segura do Reels.
7. Versão log: grade em 100, 200, 300, 400 e 500, selo LOG na legenda e "escala log" na linha de fonte.
8. Texto mínimo de 40 px (o `marca.md` aceita 32 px). Linha de fonte com 28 px.
