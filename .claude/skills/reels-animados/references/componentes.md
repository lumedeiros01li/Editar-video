# Plano e componentes

## Estrutura

```json
{
  "estilo": "brutalista",
  "audio": "voz_cortado.m4a",
  "transcricao": "transcricao.json",
  "fps": 30,
  "cauda": 1.2,
  "musica": {"ativa": true, "bpm": 96, "volume": -28},
  "legenda": {"max_palavras": 4},
  "sfx": true,
  "volume_sfx": 0,
  "cenas": [
    {"id": "c1", "fundo": "cinza", "elementos": []},
    {"id": "c2", "ancora": "Em doze meses", "fundo": "preto", "transicao": "bloco", "elementos": []}
  ]
}
```

- `estilo`: `"blueprint"` ou `"brutalista"`. Um por vídeo. Sem o campo, o `preparar_plano.py` escolhe pelo conteúdo e explica numa NOTA.
- `fundo`: no Blueprint só `papel` (pode omitir). No Brutalista `cinza` (padrão), `preto` ou `roxo`.
- `transicao`: Blueprint `corte`, `cortina`, `lateral`, `empurra`. Brutalista `corte` ou `bloco`.
- `cauda`: segundos depois da última fala, para o CTA respirar.
- `musica.bpm`: 84 a 104. Mais lento para tema sério, mais rápido para lista e dica.
- `musica.estilo`: sem o campo, segue o estilo do vídeo (`suave` no Blueprint, `pulso` no Brutalista).

## Tempo: âncoras de texto

Copie trechos curtos de `transcricao.txt` (2 a 4 palavras, do jeito que foram transcritos):

| Campo | Efeito |
|---|---|
| `"ancora": "mil reais"` | Começa quando essa sequência é dita (procura depois da âncora anterior) |
| `"palavra": 17` | Começa na palavra de índice 17 |
| `"inicio": 0` | Segundos absolutos. Só na primeira cena |
| `"ate_ancora": "e o imposto"` | Termina 0,35 s depois desse trecho |
| `"dur": 2.5` | Duração |

A cena vai da sua âncora até a âncora da próxima. Elemento sem fim definido fica até o fim da cena e sai junto com a transição. Elemento sem âncora entra logo após o início da cena.

Itens de `icones`, `lista`, `linhas`, `colunas`, `marcos` e `segmentos` aceitam `"ancora"` para entrar quando são ditos.

## Campos que valem para todos os elementos

| Campo | Efeito |
|---|---|
| `"etiqueta": "pergunta"` | Rótulo em Mono colado ao elemento. Até 4 palavras e 28 caracteres. Blueprint: `// pergunta` em roxo. Brutalista: `[ PERGUNTA ]` em caixa alta. |
| `**palavra**` | Destaque. Blueprint: Barlow semibold sobre o título light. Brutalista: bloco roxo que varre por trás, texto branco. A pontuação depois do `**` fica fora. Um por elemento. |
| `"pos"` | `alto`, `centro` (padrão) ou `baixo`. `"y"` em px força a posição. |

O motor troca o visual de cada componente pelo estilo: no Brutalista, número, comparação, gráfico, moedas, lista, linha do tempo, rosca e CTA viram cartão branco com borda e sombra dura. O plano só muda nos componentes exclusivos (carimbo e sticker, do Brutalista).

## Componentes

### frase
Texto cinético, palavra por palavra. `tamanho`: `g` (até 6 palavras), `m` (até 10), `p` (até 16). No Brutalista o limite é 8 palavras em qualquer tamanho, em caixa alta, e cada palavra entra de uma vez. "R$ 10" conta como uma palavra. `**destaque**` na cor da cena, `\n` quebra linha. `sincronizar: true` faz cada palavra entrar quando é dita (as palavras da frase precisam aparecer na fala, na mesma ordem). `sub`: linha menor embaixo. `alinhar: "centro"` só quando a frase é curta e está sozinha.
```json
{"tipo": "frase", "inicio": 0, "tamanho": "g", "pos": "alto", "texto": "Dinheiro\n**parado**?", "ancora": "dinheiro parado", "sincronizar": true}
```

### numero
Número gigante que conta (suave no Blueprint, em 6 degraus no Brutalista). Até 8 caracteres, acima disso a fonte encolhe. `topo`, `rotulo`, `fonte`. `contar: false` para anos. `"caneta"` (só Blueprint): `"sublinha"` (padrão), `"circula"` para o resultado principal, `false` para desligar. No Brutalista o número vira a caixa de resposta limão e o `topo` vira rótulo em Mono ("Resposta =").
```json
{"tipo": "numero", "ancora": "quinze por cento", "topo": "Selic hoje", "valor": "15%", "rotulo": "ao ano", "fonte": "Banco Central, Copom set/2026"}
```

### conta (os dois estilos)
Quadro de equação em JetBrains Mono, o coração de todo Reel de conta e simulação. 2 a 5 linhas, cada uma ancorada no número falado.

Cada linha usa `rotulo` (à esquerda) e `valor` (à direita), até 26 caracteres somados, ou `texto` numa coluna só (até 24). Parênteses no rótulo ficam apagados. Uma linha com `"resultado": true` fecha a conta.
- Blueprint: caixa de borda roxa fina, linhas escritas caractere por caractere, linha tracejada antes do resultado, resultado em limão com traço de caneta embaixo do valor (`"caneta": "circula"` circula, `false` desliga).
- Brutalista: linhas soltas no fundo, régua preta grossa, resultado numa caixa limão com borda preta e sombra roxa. Use `"rotulo": "Resposta ="` no resultado.

Precisa de `aviso` no mesmo trecho, ou `fonte` se o dado for real. Em `texto` numa coluna só, o resultado tem até 16 caracteres.
```json
{"tipo": "conta", "linhas": [
  {"rotulo": "renda mensal", "valor": "10.000", "ancora": "dez mil"},
  {"rotulo": "× 12 meses", "valor": "120.000"},
  {"rotulo": "÷ taxa (6% a.a.)", "valor": "0,06"},
  {"rotulo": "capital", "valor": "R$ 2.000.000", "resultado": true}]}
```
Nas linhas sem âncora o motor espaça 0,8 s. Ancore cada uma no número dito.

### carimbo (só Brutalista)
Uma palavra de até 8 letras carimbada girada, com batida forte e tremor. `destaque: true` deixa limão (use para FATO). `giro` em graus (padrão -7).
```json
{"tipo": "carimbo", "pos": "alto", "texto": "MITO"},
{"tipo": "carimbo", "pos": "alto", "texto": "FATO", "destaque": true, "giro": 6}
```

### sticker (só Brutalista)
Etiqueta limão girada, até 4 palavras, para ressalva ou ironia curta. Alinha à direita (`"alinhar": "esquerda"` para o outro lado). Posicione com `y` perto do elemento que comenta. Não conta no limite de 2 elementos por cena.
```json
{"tipo": "sticker", "ancora": "parado", "texto": "spoiler: depende", "y": 760}
```

### icone
Um ícone grande, com rótulo opcional. Blueprint: anel roxo que se abre e traços que se desenham. Brutalista: quadrado branco com borda e sombra.
```json
{"tipo": "icone", "icone": "grafico_desce", "rotulo": "A inflação **come**\nseu rendimento"}
```
Ícones: alerta, alvo, ampulheta, calendario, carro, cartao, carteira, casa, check, cofre, dolar, escudo, familia, grafico_desce, grafico_sobe, imposto, lampada, maleta, moeda, pessoa, porcentagem, relogio, saude, xis.

### icones
2 a 4 ícones lado a lado, cada um entrando na sua âncora.
```json
{"tipo": "icones", "itens": [{"icone": "calendario", "rotulo": "Prazo", "ancora": "prazo"}, {"icone": "ampulheta", "rotulo": "Liquidez", "ancora": "liquidez"}]}
```

### personagem
Figura simples da marca para histórias. Corpo roxo no Blueprint, limão com contorno preto no Brutalista. `nome`, `descricao`, `humor` (`feliz`, `preocupado`, `neutro`), `balao` com `balao_ancora`. Use `pos: "baixo"` com uma frase no alto.
```json
{"tipo": "personagem", "pos": "baixo", "nome": "Ana, 32", "descricao": "CLT, quer sair do aluguel", "humor": "preocupado", "balao": "Tá na poupança!", "balao_ancora": "poupança"}
```

### moedas
1 a 3 pilhas que crescem moeda por moeda. `moedas` (até 22) é a altura visual: mantenha a proporção dos valores. `texto` aparece no topo quando a pilha termina.
```json
{"tipo": "moedas", "titulo": "R$ 1.000 em 12 meses", "colunas": [
  {"rotulo": "Poupança", "moedas": 10, "texto": "R$ 1.060", "ancora": "mil reais na poupança"},
  {"rotulo": "CDI", "moedas": 15, "texto": "R$ 1.110", "ancora": "no CDI"}]}
```

### comparacao
Barras horizontais com valor contando. `valor` define o tamanho, `texto` o que aparece. Barras comuns roxas, a de `destaque: true` limão.
```json
{"tipo": "comparacao", "titulo": "Custo por ano", "linhas": [
  {"rotulo": "Taxa 2%", "valor": 2000, "texto": "R$ 2.000", "ancora": "dois por cento"},
  {"rotulo": "Taxa 0,5%", "valor": 500, "texto": "R$ 500", "destaque": true, "ancora": "meio por cento"}]}
```

### grafico
Linha que se desenha (crescimento no tempo). Blueprint: papel milimetrado, eixos que se desenham, valor final circulado pela caneta. Brutalista: área limão com borda preta, a linha avança um ponto por vez. `valores`, `rotulos` (primeiro e último), `final`, `desenho` (s).
```json
{"tipo": "grafico", "titulo": "A diferença em **10 anos**", "valores": [0, 95, 240, 440, 700, 1040], "rotulos": ["ano 0", "ano 10"], "final": "+R$ 1.040", "ancora": "em dez anos"}
```

### lista
Até 4 itens de até 5 palavras com check. Itens futuros aparecem como esqueleto.
```json
{"tipo": "lista", "titulo": "Antes de investir", "itens": [{"texto": "Prazo", "ancora": "prazo"}, {"texto": "Liquidez", "ancora": "liquidez"}]}
```

### linha_tempo
Até 4 marcos verticais. `quando` (curto, grande) e `texto`.
```json
{"tipo": "linha_tempo", "marcos": [
  {"quando": "25 anos", "texto": "começa com R$ 300/mês", "ancora": "aos vinte e cinco"},
  {"quando": "45 anos", "texto": "a curva acelera", "ancora": "aos quarenta e cinco"}]}
```

### rosca
2 a 4 fatias. `centro` é o número grande no meio. A fatia com `destaque: true` usa a cor de destaque.
```json
{"tipo": "rosca", "centro": "30%", "segmentos": [
  {"rotulo": "Imposto", "valor": 30, "destaque": true, "ancora": "trinta por cento"},
  {"rotulo": "Seu", "valor": 70}]}
```

### cta
Chamada final. Blueprint: Barlow light, `[[PALAVRA]]` em chip limão. Brutalista: Archivo Black em caixa alta, `[[PALAVRA]]` em chip preto com texto limão. Até 8 palavras. A legenda some enquanto aparece.
```json
{"tipo": "cta", "ancora": "comenta", "texto": "Comenta [[RESERVA]]"}
```

### aviso
Obrigatório em cena com exemplo numérico ou rentabilidade. Textos em `qualidade.md`.
```json
{"tipo": "aviso", "texto": "Exemplo ilustrativo, não é promessa de resultado."}
```

## Revisão da transcrição

Antes do plano, edite `transcricao.json`: grafia, siglas e números ditos por extenso viram algarismos (coloque o número na primeira palavra, estenda o `fim` dela até a última e deixe as outras com `"texto": ""`). Se juntar palavras, use o texto novo nas âncoras.
