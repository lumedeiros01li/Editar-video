# Reel animado: R$ 100 em 2000 (@lucasmedeiros.ai)

MP4 de 17,4 s (17 s de roteiro + 0,4 s de rebobinagem para o loop), 1080x1920, 30 fps, eixo log. Música e efeitos sintetizados em código.

## Como rerodar

```
python3 extrair_dados.py   # planilha -> dados.json (confere contra os valores calculados da própria planilha)
node render.mjs            # quadros + áudio + out/reel-r100-em-2000.mp4
node verificar.mjs         # valores, flashes, ranking, limites, colisões, loop, sincronia, ffprobe, loudness
node contato.mjs           # folhas de contato em out/contact-sheets/
```

## Roteiro implementado

| Tempo | Na tela |
|---|---|
| 0 a 2 s | `[ R$ 100 EM 2000 ]`, "QUEM VIROU MAIS?", linhas paradas em 100 com os nomes em ordem neutra |
| 2 a 5 s | corrida até 2007 |
| 5 a 6 s | 2008 em câmera lenta, flash "2008: IBOVESPA -41%" |
| 6 a 8,5 s | até 2017 |
| 8,5 a 9,5 s | 2018 em câmera lenta, flash "2018: S&P PASSA A POUPANÇA" |
| 9,5 a 11,5 s | até set/2026, flash "2024: DÓLAR +28%" |
| 11,5 a 12,5 s | congelado, "QUAL FICOU EM 1º?" |
| 12,5 a 15,5 s | valores do último ao primeiro a cada 0,6 s (inflação em cinza junto com a poupança) |
| 15,5 a 17 s | ranking parado, "POUPANÇA: CERCA DE 1% AO ANO ACIMA DA INFLAÇÃO" e "LEIA A LEGENDA" |
| 17 a 17,4 s | rebobina até o quadro 0 (último quadro = primeiro) |

Todos os números (valores, flashes, ano da ultrapassagem e o "1% ao ano") são calculados do `dados.json`.

## Fonte dos dados

Planilha `fonte-dados/comparacao_ativos_25_anos.xlsx` (recebida em 24/10/2026, SHA256 em `dados.json`). Base 100 em 31/12/2000, até 30/09/2026. As fontes por série estão na aba "Fontes e notas" e copiadas em `dados.json`.

## Ressalvas

1. Boa parte das séries vem de compiladores secundários (Clube dos Poupadores, meusdividendos, Seu Dinheiro, Nomad, datahub). A própria planilha pede conferência contra BCB, Yahoo Finance ou Investing antes de publicar.
2. O roteiro dizia "S&P SÓ PASSA A POUPANÇA AQUI" em 2018. Pelos dados, o S&P em R$ passou a poupança em 2002 (122 x 119) e voltou para trás. Em 2018 passa de vez (382 x 377). O texto ficou "2018: S&P PASSA A POUPANÇA". A margem de 2018 é pequena e depende da média de dezembro usada como proxy.
3. O rótulo é "CDI", que é a série da planilha. O roteiro chamava de Selic.
4. "DÓLAR +28%" (2024) vem da Ptax de fim de ano compilada pelo Clube dos Poupadores. Confirmar no BCB.
5. Aviso de rentabilidade no texto padrão do `compliance.md`, mais "bruto" e "*Sem dividendos" para Ibovespa e S&P.
6. Nas ultrapassagens, dois rótulos se cruzam por cerca de 3 quadros. Somando tudo, 0,87 s do vídeo.
