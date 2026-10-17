# Roteiro e gravação

O roteiro é metade do vídeo. Animação boa não salva fala longa, abstrata ou sem tensão.

## Antes de escrever

Confirme em uma mensagem, só o que faltar:
1. Tema e a única ideia que a pessoa deve levar.
2. Formato (abaixo). Sem preferência, proponha o que serve melhor ao tema.
3. CTA: "comenta PALAVRA" (qual palavra e o que a pessoa recebe) ou "me chama".
4. Dados: número que dependa de mercado (Selic, IPCA, CDI, dólar, tabela de IR) precisa de valor, fonte e data conferidos antes de escrever. Sem isso, `[CONFERIR: dado, fonte e data]`.

## Formatos que funcionam em animação

| Formato | Estrutura | Bom para |
|---|---|---|
| História de personagem | Personagem com um problema comum, a decisão, a consequência, a lição | Erros financeiros, proteção, planejamento |
| A conta | Pergunta, o número que choca, a conta mostrada, o que fazer | Inflação, juros compostos, custo de oportunidade |
| Mito e fato | Crença comum, por que parece certa, o fato, a regra prática | Poupança, FGC, previdência |
| Passo a passo | Promessa clara, 3 passos com ícone, fechamento | Reserva de emergência, organização |
| Linha do tempo | Antes, virada, depois | Aposentadoria, objetivos de longo prazo |

## Estrutura e tempo

- 30 a 60 s. A fala do Lucas, depois dos cortes, roda perto de 2,5 palavras por segundo: 45 s cabem 110 palavras.
- Gancho nos 2 primeiros segundos: pergunta direta, número inesperado ou contradição. Nunca "Oi, pessoal" ou "Hoje eu vou falar".
- Uma ideia por cena, 3 a 6 s por cena. Cena com mais de duas frases faladas vira duas cenas.
- Frases curtas, uma informação por frase. Número sempre redondo e falado do jeito que deve aparecer.
- Fechamento com CTA único.

## Formato de entrega do roteiro

Entregue dois blocos.

**Roteiro com cenas** (para aprovar e para montar o plano depois):

```
[C1 · branco · personagem Ana preocupada + frase "Dinheiro parado?"]
Você deixa dinheiro parado na poupança?

[C2 · roxo · cortina · ícone inflação]
Em doze meses, a inflação comeu parte dele.
...
```

**Texto para gravar** (só a fala, uma frase por linha, sem marcações). É o que o Lucas lê.

## Regras de texto

- Voz do Lucas: direta, próxima, sem jargão sem explicação. Sigla explicada na primeira vez quando o público é iniciante.
- Sem travessão e sem ponto e vírgula. Frases simples.
- Compliance antes de entregar: sem promessa de retorno, sem "garantido", sem "sem risco", nunca "blindagem", sem ativo ou fundo específico com linguagem de compra, todo dado real com fonte e data, exemplo numérico declarado como ilustrativo.
- Passe o texto pela skill humanizer (se instalada) para tirar padrões de texto de IA: simetria, conectivos empilhados, frases de efeito vazias.

## Guia de gravação para o Lucas

Mande junto com o texto para gravar:

- Celular a um palmo da boca, em cômodo pequeno com cortina, sofá ou roupas (absorvem eco). Nada de ventilador ou ar ligado.
- Grave em sequência. Errou, pare 2 segundos e repita a frase inteira. Os cortes removem as pausas, e a frase repetida deve ser apagada na revisão da transcrição.
- Fale um pouco mais animado que numa conversa. Áudio sem vídeo perde energia.
- Pode trocar palavras para soar natural. O plano se ancora no que foi falado, não no roteiro.
- Envie o arquivo original (m4a, wav ou mp3), sem compressão de WhatsApp.

## Quando o áudio chega

Depois da transcrição, compare com o roteiro.

- **Frase repetida por erro:** ache na `transcricao.txt` o início e o fim da tentativa ruim e remova o trecho do áudio limpo. Depois transcreva de novo.
  ```bash
  ffmpeg -i voz_cortado.m4a -af "aselect='not(between(t,INICIO,FIM))',asetpts=N/SR/TB" -c:a aac voz_final.m4a
  ```
- **Improviso que muda a ordem ou o conteúdo:** ajuste o plano à fala real, não o contrário.
- **Termo proibido falado:** não dá para esconder com animação. Peça ao Lucas para regravar a frase.
