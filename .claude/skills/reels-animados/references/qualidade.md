# Loop de qualidade

Nada vai para o Lucas sem passar por aqui. O render completo é a etapa cara. A folha de contato custa segundos e mostra 90% dos problemas.

## O ciclo

1. `node render.mjs plano_resolvido.json --folha --guias` e **abra a imagem** com a ferramenta de visualização. Olhar de verdade: ler cada quadro, não só confirmar que o arquivo existe. O primeiro quadro da folha, com borda limão, é a imagem de referência do estilo (`references/estilos/`). Compare cada quadro com ela: peso da borda e da sombra, tamanho do texto, quanto limão aparece, densidade do quadriculado. Se a referência não estiver na pasta, o render avisa e a comparação fica só pelas regras escritas.
2. Gere a tira de movimento do gancho e de 2 transições: `--movimento <inicio> --dur 0.6`. Ela mostra 10 quadros a 15 qps. Confira se a entrada é limpa, se a mola não passa do ponto e se a transição não deixa quadro vazio.
3. Dê nota de 1 a 10 em cada critério abaixo (sete critérios). Escreva a nota e o motivo em uma linha cada.
4. Corrija os 3 piores problemas. Mexa no plano, rode `preparar_plano.py` de novo e volte ao passo 1.
5. Repita até toda nota ser 8 ou mais. Limite de 4 voltas. Se travar, mostre ao Lucas a folha e diga qual critério não sobe e por quê.
6. Só então rode `audio.py` e o render final. Antes, ouça a trilha sozinha (`audio.py --so-trilha`) se o Lucas quiser aprovar o clima.

## Critérios

**Gancho nos 2 primeiros segundos**
- 10: no quadro 0 já há frase, número ou personagem que cria tensão (pergunta, contradição, número). Algo se move antes de 0,5 s.
- 8: elemento claro no quadro 0, sem tensão forte.
- 5: tela só com fundo e legenda nos 2 primeiros segundos.

**Leitura em tela de celular**
- 10: todo texto acima de 46 px, nada nas faixas vermelhas, cada cena entendida em menos de 1 s, legenda nunca encostando em elemento.
- 8: tudo legível, uma cena um pouco densa.
- 5: dois elementos disputando a mesma área, frase longa demais, legenda cobrindo elemento.

**Qualidade do movimento** (tira de movimento)
- Blueprint 10: painéis e traços se desenham em até 0,5 s, conteúdo sobe sem passar do ponto, nada quica, a caneta fecha o círculo depois que o número para.
- Brutalista 10: cartão assenta na sombra em 3 quadros, tremor curto (6 quadros) e só na entrada de cartão, saída é corte seco, nenhuma transição suave.
- 8: tudo limpo, uma entrada um pouco lenta ou um tremor a mais.
- 5: elemento pulando de posição, quique no Blueprint, fade no Brutalista, saída mais lenta que a entrada.

**Variedade**
- 10: pelo menos 5 tipos de componente num vídeo de 30 a 45 s, nenhum trecho de 4 s sem novidade (o `preparar_plano.py` mede). Blueprint: 3 transições diferentes. Brutalista: os três fundos aparecem e se alternam.
- 8: 4 tipos, ritmo dentro da regra.
- 5: o mesmo componente repetido, fundo igual o vídeo todo, trecho morto acima de 4 s.

**Fidelidade ao estilo** (compare com a referência)
- 10: um estilo só, parece da mesma família da imagem de referência, só os fundos do estilo, um destaque limão por cena, o par de fontes certo, nenhum padrão proibido de `direcao-de-arte.md`.
- 8: um detalhe fora (ex.: dois destaques na mesma frase, etiqueta longa).
- 5: componente do outro estilo, cor fora da paleta, glow, seta dupla, logo, partículas, canto arredondado no Brutalista.

**Sincronia do som**
- 10: cada cena e elemento ancorado na fala, frases com `sincronizar`, acertos na grade da trilha, efeitos discretos, trilha nunca disputando com a voz.
- 8: um elemento com tempo solto que poderia estar ancorado.
- 5: elemento entrando antes do assunto, efeito mais alto que a fala, trilha competindo com a voz.

**Fidelidade à fala** (específico de animação)
- 10: cada cena ilustra exatamente o que está sendo dito, metáfora visual clara (moedas para dinheiro acumulando, rosca para parte de um todo).
- 8: uma cena genérica (ícone que serve para qualquer frase).
- 5: animação contando uma coisa e a voz outra.

## Portão de compliance (não tem nota, é sim ou não)

Se qualquer item falhar, o vídeo não sai.

- [ ] Nenhuma promessa de retorno ou prazo na tela ("garantido", "sem risco", "renda certa", "dobre").
- [ ] Nunca a palavra "blindagem".
- [ ] Todo dado real tem fonte e data no campo `fonte`. Todo exemplo inventado tem `aviso`.
- [ ] Nenhum fundo, ativo, emissor ou ticker com linguagem de compra.
- [ ] Nenhum logo ou marca na tela, nenhuma seta dupla.
- [ ] Personagem não representa cliente real nem promete resultado.
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

Esperado: 1080 x 1920, durações de vídeo e áudio iguais (diferença menor que 0,1 s), cerca de -14 LUFS (a proteção de pico pode deixar até 1 LU abaixo). Extraia 3 quadros do arquivo final (`ffmpeg -ss T -i final.mp4 -frames:v 1 q.png`) e olhe: o que sai do encoder às vezes difere da prévia.
