# Loop de qualidade

Nada vai para o Lucas sem passar por aqui. O render completo é a etapa cara. A folha de contato custa segundos e mostra 90% dos problemas.

## O ciclo

1. `node render.mjs plano_resolvido.json --folha --guias` e **abra a imagem** com a ferramenta de visualização. Olhar de verdade: ler cada quadro, não só confirmar que o arquivo existe. O primeiro quadro da folha, com borda limão, é a imagem de referência do estilo (`references/estilos/`). Compare cada quadro com ela: peso da borda e da sombra, tamanho do texto, quanto limão aparece, densidade do quadriculado. Se a referência não estiver na pasta, o render avisa e a comparação fica só pelas regras escritas.
2. Para as 2 entradas mais importantes (gancho e o cartão principal), gere a tira de movimento: `--movimento <inicio> --dur 0.6`. Ela mostra 10 quadros a 15 qps. Confira se a entrada é limpa e se a mola não passa do ponto.
3. Dê nota de 1 a 10 em cada critério abaixo. Escreva a nota e o motivo em uma linha cada.
4. Corrija os 3 piores problemas. Mexa no plano, rode `preparar_plano.py` de novo e volte ao passo 1.
5. Repita até toda nota ser 8 ou mais. Limite de 4 voltas. Se travar, mostre ao Lucas a folha e diga qual critério não sobe e por quê.
6. Só então rode `audio.py` e o render final.

## Critérios

**Gancho nos 2 primeiros segundos**
- 10: no quadro 0 já há título ou palavra de impacto que cria tensão (pergunta, contradição, número). Algo se move antes de 1 s.
- 8: título claro no quadro 0, sem tensão forte.
- 5: só legenda nos 2 primeiros segundos.

**Leitura em tela de celular**
- 10: todo texto acima de 46 px, nada nas faixas vermelhas, contraste alto em todos os quadros, cada cartão lido em menos de 1 s.
- 8: tudo legível, um cartão um pouco denso.
- 5: texto sobre área clara do fundo sem véu, cartão com mais de 12 palavras, legenda cobrindo o cartão.

**Qualidade do movimento** (tira de movimento)
- Blueprint 10: painéis e traços se desenham em até 0,5 s, conteúdo sobe sem passar do ponto, nada quica, a caneta fecha o círculo depois que o número para.
- Brutalista 10: cartão assenta na sombra em 3 quadros, tremor curto (6 quadros) e só na entrada de cartão, saída é corte seco, nenhuma transição suave.
- 8: tudo limpo, uma entrada um pouco lenta ou um tremor a mais.
- 5: elemento pulando de posição, quique no Blueprint, fade no Brutalista, saída mais lenta que a entrada.

**Variedade**
- 10: pelo menos 4 tipos de componente diferentes num vídeo de 30 s, zoom de corte ativo, nenhum trecho de 4 s sem novidade (o `preparar_plano.py` mede).
- 8: 3 tipos, ritmo dentro da regra.
- 5: o mesmo cartão repetido, ou trecho morto acima de 4 s.

**Fidelidade ao estilo** (compare com a referência)
- 10: um estilo só, parece da mesma família da imagem de referência, só a paleta única, o par de fontes certo do estilo, limão só no destaque, nenhum padrão proibido de `direcao-de-arte.md`.
- 8: um detalhe fora (ex.: dois destaques limão no mesmo cartão, etiqueta longa).
- 5: componente do outro estilo, cor fora da paleta, glow, seta dupla, logo, canto arredondado no Brutalista.

**Sincronia com a fala**
- 10: cada elemento entra junto da palavra que ilustra (âncora por índice), cada item de lista no instante em que é dito, a pílula da legenda acompanha a fala.
- 8: um elemento com tempo absoluto que poderia estar ancorado.
- 5: cartão entrando antes do assunto ou depois que o Lucas já mudou de assunto.

## Portão de compliance (não tem nota, é sim ou não)

Se qualquer item falhar, o vídeo não sai.

- [ ] Nenhuma promessa de retorno ou prazo na tela ("garantido", "sem risco", "renda certa", "dobre").
- [ ] Nunca a palavra "blindagem".
- [ ] Todo dado real tem fonte e data no campo `fonte`. Todo exemplo inventado tem `aviso`.
- [ ] Nenhum fundo, ativo, emissor ou ticker com linguagem de compra.
- [ ] Nenhum logo ou marca na tela, nenhuma seta dupla.
- [ ] Se o `preparar_plano.py` avisou termo sensível na fala, o Lucas foi avisado (a fala não se edita, se regrava ou se corta).

Avisos de mercado para usar no componente `aviso`:

| Situação | Texto |
|---|---|
| Simulação ou exemplo numérico | Exemplo ilustrativo, não é promessa de resultado. |
| Rentabilidade passada | Rentabilidade passada não é garantia de rentabilidade futura. |
| Rentabilidade sem imposto | Rentabilidade bruta, antes de impostos. |
| Fundo de investimento | Fundos não têm garantia do FGC. Leia a lâmina e o regulamento. |

## Conferência do render final

Depois do render completo:

```bash
ffprobe -v error -show_entries stream=codec_type,width,height,duration -of compact final.mp4
ffmpeg -hide_banner -i final.mp4 -af ebur128 -f null - 2>&1 | grep "I:"
```

Esperado: 1080 x 1920, durações de vídeo e áudio iguais (diferença menor que 0,1 s), cerca de -14 LUFS. Extraia 3 quadros do arquivo final (`ffmpeg -ss T -i final.mp4 -frames:v 1 q.png`) e olhe: o que sai do encoder às vezes difere da prévia.
