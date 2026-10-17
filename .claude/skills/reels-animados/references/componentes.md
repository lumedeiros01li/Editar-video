# Plano e componentes

## Estrutura

```json
{
  "audio": "voz_cortado.m4a",
  "transcricao": "transcricao.json",
  "fps": 30,
  "cauda": 1.2,
  "musica": {"ativa": true, "bpm": 96, "estilo": "pulso", "volume": -28},
  "legenda": {"max_palavras": 4},
  "sfx": true,
  "volume_sfx": 0,
  "cenas": [
    {"id": "c1", "fundo": "branco", "elementos": []},
    {"id": "c2", "ancora": "Em doze meses", "fundo": "roxo", "transicao": "cortina", "elementos": []}
  ]
}
```

- `cauda`: segundos depois da última fala, para o CTA respirar.
- `musica.bpm`: 84 a 104. Mais lento para tema sério, mais rápido para lista e dica.

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

## Componentes

### frase
Texto cinético, palavra por palavra. `tamanho`: `g` (124 px, até 6 palavras), `m` (96 px, até 10), `p` (70 px, até 16). `**destaque**` na cor da cena, `\n` quebra linha. `sincronizar: true` faz cada palavra entrar quando é dita (as palavras da frase precisam aparecer na fala, na mesma ordem). `sub`: linha menor embaixo. `alinhar: "centro"` só quando a frase é curta e está sozinha.
```json
{"tipo": "frase", "inicio": 0, "tamanho": "g", "pos": "alto", "texto": "Dinheiro\n**parado**?", "ancora": "dinheiro parado", "sincronizar": true}
```

### numero
Número gigante que conta. Até 8 caracteres. `topo`, `rotulo`, `fonte`. `contar: false` para anos.
```json
{"tipo": "numero", "ancora": "quinze por cento", "topo": "Selic hoje", "valor": "15%", "rotulo": "ao ano", "fonte": "Banco Central, Copom set/2026"}
```

### icone
Um ícone grande num disco, com rótulo opcional.
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
Figura simples da marca para histórias. `nome`, `descricao`, `humor` (`feliz`, `preocupado`, `neutro`), `balao` com `balao_ancora`. Use `pos: "baixo"` com uma frase no alto.
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
Barras horizontais com valor contando. `valor` define o tamanho, `texto` o que aparece, `destaque: true` pinta de destaque.
```json
{"tipo": "comparacao", "titulo": "Custo por ano", "linhas": [
  {"rotulo": "Taxa 2%", "valor": 2000, "texto": "R$ 2.000", "ancora": "dois por cento"},
  {"rotulo": "Taxa 0,5%", "valor": 500, "texto": "R$ 500", "destaque": true, "ancora": "meio por cento"}]}
```

### grafico
Linha que se desenha (crescimento no tempo). `valores`, `rotulos` (primeiro e último), `final`, `desenho` (s).
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
Caixa de chamada. `[[PALAVRA]]` vira chip. Até 8 palavras. A legenda some enquanto aparece.
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
