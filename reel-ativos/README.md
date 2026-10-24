# Reel animado: R$ 100 em 2000 (@lucasmedeiros.ai)

Duas versões, `out/reel-r100-em-2000-log.mp4` e `out/reel-r100-em-2000-linear.mp4`: 16,4 s (16 s de roteiro + 0,4 s de rebobinagem para o loop), 1080x1920, 30 fps. Música e efeitos sintetizados em código, iguais nas duas.

## Como rerodar

```
python3 extrair_dados.py   # planilha -> dados.json (confere contra os valores calculados da própria planilha)
node render.mjs                 # as duas versões (ou --eixo=log / --eixo=linear)
node verificar.mjs --eixo=log   # valores, flashes, ranking, limites, colisões, loop, sincronia, ffprobe, loudness
node contato.mjs --eixo=log     # folhas de contato em out/contact-sheets/<eixo>/
```

## Roteiro implementado

| Tempo | Na tela |
|---|---|
| 0 a 1 s | `[ R$ 100 EM 2000 ]`, "QUEM VIROU MAIS?", linhas paradas em 100 com os nomes em ordem neutra |
| 1 a 4 s | corrida até 2007 |
| 4 a 5 s | 2008 em câmera lenta, flash "2008: IBOVESPA -41%" |
| 5 a 7,5 s | até 2017 |
| 7,5 a 8,5 s | 2018 em câmera lenta, flash "2018: S&P PASSA A POUPANÇA" |
| 8,5 a 10,5 s | até set/2026, flash "2024: DÓLAR +28%" |
| 10,5 a 11,5 s | congelado, "QUAL FICOU EM 1º?" |
| 11,5 a 14,5 s | valores do último ao primeiro a cada 0,6 s (inflação em cinza junto com a poupança) |
| 14,5 a 16 s | ranking parado, "POUPANÇA: CERCA DE 1% AO ANO ACIMA DA INFLAÇÃO" e "LEIA A LEGENDA" |
| 16 a 16,4 s | rebobina até o quadro 0 (último quadro = primeiro) |

O cartão ocupa a caixa marcada no print (x 90 a 990, de y 362 até o rodapé em 1678). A etiqueta, o selo LOG e o ano ficam na faixa de cima do cartão; no ranking, a faixa vira o "LEIA A LEGENDA". Na ponta de cada linha há um ícone (banco = CDI, barras = ouro, bandeira do Brasil = Ibovespa, bandeira dos EUA = S&P 500, porquinho = poupança, carrinho = inflação), e a legenda 2 x 3 embaixo do gráfico liga ícone e nome e recebe os valores na revelação. Área útil do gráfico: 682 x 856 px.

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
