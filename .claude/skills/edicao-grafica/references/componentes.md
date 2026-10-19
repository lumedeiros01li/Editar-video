# Componentes do plano

O plano (`plano.json`) diz o que aparece e quando. O motor decide como anima. Use os índices de `transcricao.txt` para ancorar tudo na fala.

## Estrutura do plano

```json
{
  "estilo": "blueprint",
  "video": "gravacao_cortado.mp4",
  "transcricao": "transcricao.json",
  "relatorio_cortes": "gravacao_cortado_cortes.json",
  "fps": 30,
  "foco": [540, 760],
  "legenda": {"max_palavras": 4},
  "zoom_cortes": {"ativo": true, "escala": 1.08},
  "eventos": [],
  "audio": {"sfx": true, "volume_sfx": 0, "musica": null}
}
```

- `estilo`: `"blueprint"` ou `"brutalista"`. Um por vídeo. Sem o campo, o `preparar_plano.py` escolhe pelo conteúdo e explica numa NOTA (regra em `direcao-de-arte.md`).
- `foco`: ponto do rosto em px (x, y) no quadro 1080 x 1920. Os zooms crescem a partir dele. Descubra olhando um quadro do vídeo.
- `legenda.ocultar`: lista de intervalos `[[ini, fim]]` em segundos para esconder a legenda (ex.: quando a palavra de impacto já mostra a frase).
- `legenda.ativa: false` desliga a legenda.

## Tempo de cada evento

Use âncoras na fala sempre que possível:

| Campo | Significado |
|---|---|
| `"palavra": 12` | Entra 2 quadros antes da palavra 12 começar |
| `"ate_palavra": 20` | Sai 0,35 s depois da palavra 20 terminar (`"segura": 0.6` muda a folga) |
| `"inicio"`, `"fim"` | Segundos absolutos. Use só no título do quadro 0 |
| `"dur"` | Duração em segundos a partir do início |

Sem fim definido, cada tipo tem duração padrão (emoji 1,2 s, palavra 1,4 s, número 3 s, título 2,6 s, CTA até o fim).

Itens de lista e linhas de comparação também aceitam `"palavra"`, para cada item entrar quando o Lucas fala dele.

## Campos que valem para todos os cartões

| Campo | Efeito |
|---|---|
| `"etiqueta": "pergunta"` | Rótulo em Mono colado ao elemento. Até 4 palavras e 28 caracteres. Blueprint: `// pergunta` em roxo. Brutalista: `[ PERGUNTA ]` em caixa alta. |
| `**palavra**` | Destaque. Blueprint: Barlow semibold sobre o título light. Brutalista: bloco roxo que varre por trás, texto branco. A pontuação depois do `**` fica fora. Um por elemento. |

O motor troca o visual de cada componente pelo estilo. O plano não muda de um estilo para o outro, só os componentes exclusivos (carimbo e sticker, do Brutalista).

## Componentes

### titulo
Gancho na área alta. Até 9 palavras no Blueprint (Barlow light) e 8 no Brutalista (em caixa alta). "R$ 10" conta como uma palavra. `\n` quebra a linha. Blueprint: painel escuro com Barlow. Brutalista: cartão branco com Archivo Black.
Use: no quadro 0, com a pergunta ou a virada do vídeo. Um por vídeo, às vezes dois.
```json
{"tipo": "titulo", "inicio": 0, "ate_palavra": 5, "texto": "Seu dinheiro está\n**parado**?"}
```

### palavra
Uma ou duas palavras gigantes no centro, até 12 letras (no Brutalista prefira até 9, acima disso a fonte encolhe). Escurece o fundo. Blueprint: letras brancas sobem e o traço limão sublinha. Brutalista: bloco roxo com borda preta e texto branco bate de uma vez, com tremor.
Use: no conceito central da frase (INFLAÇÃO, LIQUIDEZ, IMPOSTO). No máximo 2 por minuto, senão perde força.
```json
{"tipo": "palavra", "palavra": 10, "ate_palavra": 13, "texto": "Inflação"}
```

### numero
Cartão com número grande que conta até o valor (suave no Blueprint, em 6 degraus no Brutalista). `valor` em pt-BR ("R$ 1.250", "12,5%", "3x"). Rótulo até 7 palavras.
Use: quando a fala traz um número que a pessoa precisa guardar. `"contar": false` para anos e datas.
Dado real exige `"fonte"` com fonte e data. Exemplo inventado exige um `aviso` no mesmo trecho.
`"caneta"` (só Blueprint): `"sublinha"` (padrão), `"circula"` para o resultado principal do vídeo, `false` para desligar. No Brutalista o número vira a caixa de resposta limão e o `topo` vira rótulo em Mono ("Resposta =").
```json
{"tipo": "numero", "palavra": 30, "ate_palavra": 38, "topo": "Selic hoje", "valor": "15%",
 "rotulo": "ao ano", "fonte": "Fonte: Banco Central, Copom de set/2026"}
```

### comparacao
2 ou 3 barras horizontais. `valor` é o número usado no tamanho da barra. `texto` é o que aparece. As barras comuns são roxas e a de `destaque: true` é limão (a opção que o vídeo defende ou o contraste que importa).
```json
{"tipo": "comparacao", "palavra": 17, "ate_palavra": 31, "titulo": "R$ 1.000 em 12 meses",
 "linhas": [
   {"rotulo": "Poupança", "valor": 1060, "texto": "R$ 1.060", "palavra": 20},
   {"rotulo": "CDI", "valor": 1110, "texto": "R$ 1.110", "destaque": true, "palavra": 26}
 ]}
```

### grafico
Linha que se desenha. No Blueprint sobre eixos que se desenham, com o rótulo final circulado pela caneta. No Brutalista, área limão com borda preta e a linha avança um ponto por vez. `valores` em ordem, `rotulos` mostra o primeiro e o último, `final` é o rótulo do último ponto. `desenho` é a duração do traço (padrão 1,4 s).
Use: crescimento no tempo (juros compostos, inflação acumulada). Não use para comparar duas coisas, aí é `comparacao`.
```json
{"tipo": "grafico", "palavra": 34, "ate_palavra": 41, "titulo": "A diferença em **10 anos**",
 "valores": [0, 40, 95, 160, 240, 330, 440, 560, 700, 860, 1040],
 "rotulos": ["ano 0", "ano 10"], "final": "+R$ 1.040"}
```

### conta (os dois estilos)
Quadro de equação em JetBrains Mono, o coração de todo Reel de conta e simulação. 2 a 5 linhas, cada uma ancorada no número falado.

Cada linha usa `rotulo` (à esquerda) e `valor` (à direita), até 22 caracteres somados, ou `texto` numa coluna só (até 22). Parênteses no rótulo ficam apagados. Uma linha com `"resultado": true` fecha a conta.
- Blueprint: caixa de borda roxa fina, linhas escritas caractere por caractere, linha tracejada antes do resultado, resultado em limão com traço de caneta embaixo do valor (`"caneta": "circula"` circula, `false` desliga).
- Brutalista: linhas soltas no fundo, régua preta grossa, resultado numa caixa limão com borda preta e sombra roxa. Use `"rotulo": "Resposta ="` no resultado.

Precisa de `aviso` no mesmo trecho, ou `fonte` se o dado for real. Em `texto` numa coluna só, o resultado tem até 13 caracteres.
```json
{"tipo": "conta", "linhas": [
  {"rotulo": "renda mensal", "valor": "10.000", "palavra": 25},
  {"rotulo": "× 12 meses", "valor": "120.000"},
  {"rotulo": "÷ taxa (6% a.a.)", "valor": "0,06"},
  {"rotulo": "capital", "valor": "R$ 2.000.000", "resultado": true}]}
```
Nas linhas sem âncora o motor espaça 0,8 s. Ancore cada uma no número dito.

### carimbo (só Brutalista)
Uma palavra de até 8 letras carimbada girada, com batida e tremor forte. `destaque: true` deixa o carimbo limão (use para FATO). `giro` em graus (padrão -7). Posição padrão `y` 700.
Use: virada de Reel de mito contra fato. Conta como cartão: não divide a tela com outro.
```json
{"tipo": "carimbo", "palavra": 22, "ate_palavra": 24, "texto": "MITO"},
{"tipo": "carimbo", "palavra": 30, "ate_palavra": 33, "texto": "FATO", "destaque": true, "giro": 6}
```

### sticker (só Brutalista)
Etiqueta limão girada com até 4 palavras, colada perto de um cartão. Alinha à direita (`"alinhar": "esquerda"` para o outro lado), `y` padrão 560. Giro com semente entre 4 e 8 graus.
Use: comentário irônico ou ressalva curta ("spoiler: depende"). Pode dividir a tela com um cartão. No máximo 1 por cartão.
```json
{"tipo": "sticker", "palavra": 34, "ate_palavra": 39, "texto": "spoiler: depende", "y": 600}
```

### lista
Título e até 4 itens de até 5 palavras. Cada item entra na palavra em que é dito. Antes disso aparece como esqueleto (caixa vazia), o que cria expectativa.
```json
{"tipo": "lista", "palavra": 42, "ate_palavra": 55, "titulo": "Antes de investir",
 "itens": [{"texto": "Prazo", "palavra": 50}, {"texto": "Liquidez", "palavra": 52},
           {"texto": "Imposto", "palavra": 55}]}
```

### zoom
Aproximação no rosto. `modo: "suave"` (rampa de 0,4 s) para virada de tom. `modo: "seco"` (corte direto) para ênfase forte. Sem `modo`, o padrão é suave no Blueprint e seco no Brutalista. Escala entre 1,12 e 1,25.
```json
{"tipo": "zoom", "palavra": 14, "ate_palavra": 16, "escala": 1.18, "modo": "suave"}
```

### emoji
Um emoji que reforça a emoção da frase. Combina mais com o Brutalista. No Blueprint o `preparar_plano.py` avisa, porque quebra a precisão do estilo. Posição padrão acima da legenda, à direita (x 860, y 1120). Mude `x`, `y` para não cobrir o rosto.
```json
{"tipo": "emoji", "palavra": 3, "emoji": "😴"}
```

### aviso
Texto legal pequeno acima da faixa bloqueada. Obrigatório junto de exemplo numérico, rentabilidade passada ou fundo. Textos prontos na tabela de avisos em `qualidade.md`.
```json
{"tipo": "aviso", "palavra": 17, "ate_palavra": 31, "texto": "Exemplo ilustrativo, não é promessa de resultado."}
```

### cta
Chamada final. Blueprint: caixa escura com borda roxa, Barlow light, `[[PALAVRA]]` em chip limão. Brutalista: cartão branco em Archivo Black, `[[PALAVRA]]` em chip preto com texto limão. Até 8 palavras. Esconde a legenda enquanto aparece.
```json
{"tipo": "cta", "palavra": 56, "texto": "Comenta [[RESERVA]]"}
```

## Revisar a transcrição

Edite `transcricao.json` antes do plano:

- Grafia errada: troque o `texto` da palavra.
- Número por extenso: coloque o número inteiro na primeira palavra, estenda o `fim` dela até o fim da última e deixe as outras com `"texto": ""`. Os índices não mudam, a legenda pula as vazias.
  ```json
  {"i": 22, "texto": "R$ 1.060", "ini": 10.25, "fim": 11.31},
  {"i": 23, "texto": "", "ini": 10.61, "fim": 10.80},
  {"i": 24, "texto": "", "ini": 10.85, "fim": 11.31}
  ```
- Nunca mude `ini` de palavras que não juntou: o tempo vem do áudio.
