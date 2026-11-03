---
name: reels-r7
description: Edita Reels verticais no padrão R7 aprovado (caixas retas com fonte Poppins, paleta preto/branco/lima/roxo, chamada "LEIA A LEGENDA" embaixo do último texto) em duas versões, colorida e preto e branco, usando detecção facial para nunca cobrir o rosto. Use quando o usuário enviar um vídeo de fundo e um roteiro de telas com tempos (ex. "Tela 1 (0 a 3 s): ...") e pedir para editar no modelo R7, no padrão aprovado, colorido e/ou P&B.
---

# Reels R7

Gera, a partir de um vídeo e de um roteiro de telas, o padrão aprovado pelo usuário:

- **Texto em caixas retas** (cantos de 8 px, sem sombra), fonte Poppins Medium, uma caixa por linha, centralizadas.
- **Paleta:** preto `#000000`, branco `#FFFFFF`, lima `#EAF56B`, roxo `#9D74FF`.
  - Tela 1: caixas brancas, texto preto. Tela 2: caixas lima, texto preto. Linha de destaque (valor, número): caixa roxa, texto branco.
  - Chamada: caixa preta com texto lima, contorno lima, barra roxa embaixo, fonte menor (58 px).
- **Posição:** o mais perto possível do meio da tela, logo abaixo do queixo. **Nada na frente do rosto.** O rosto é detectado em todos os frames (MediaPipe) e o script informa quantos frames tiveram texto sobre o rosto (precisa ser 0).
- **Tempos:** cada tela entra em cascata e some no fim do seu tempo. A **última tela não some**. A chamada entra embaixo dela no tempo pedido e tudo fica até o fim.
- **Duas versões:** `_cor` (vídeo original) e `_pb` (vídeo em preto e branco com leve contraste, texto mantém as cores).
- Áudio original preservado. Saída 1080x1920 H.264.

## Fluxo

1. **Montar o roteiro JSON** a partir do pedido do usuário (modelo em `exemplos/medica.json`):

```json
{
  "telas": [
    {"inicio": 0, "fim": 3, "fundo": "branco",
     "linhas": ["Médica deixa", "*R$ 300 mil*", "na conta", "corrente 🏦"]},
    {"inicio": 3, "fim": 5, "fundo": "lima",
     "linhas": ["A inflação", "de 4,5% ao ano", "*pede R$ 13.500*", "só para empatar"]}
  ],
  "chamada": {"inicio": 5, "texto": "LEIA A LEGENDA 👇"}
}
```

   - Uma tela "Leia a legenda" no roteiro do usuário **não vira tela própria**: vira `chamada`, com `inicio` = tempo dessa tela.
   - Quebre as frases em linhas curtas (até ~16 caracteres), 2 a 4 linhas por tela.
   - Linha inteira entre `*asteriscos*` = destaque roxo. Use para o valor ou número principal da tela.
   - `fundo`: `branco` na 1ª tela, `lima` na 2ª. Com mais telas, alterne (também existem `roxo` e `preto`).
   - Se o usuário pedir uma tela "em vermelho", use `lima`: a paleta aprovada não tem vermelho.
   - Emojis funcionam (Noto Color Emoji).

2. **Preparar o ambiente** (uma vez por sessão, só se faltar):

```bash
pip install -q mediapipe opencv-python-headless pillow numpy
apt-get install -y -q libegl1   # o MediaPipe precisa no Linux sem GPU
```

   O modelo de rosto é baixado sozinho para `~/.cache/reels_r7/` no primeiro uso.

3. **Renderizar** as duas versões com prévia:

```bash
python3 scripts/reels_r7.py VIDEO.mp4 roteiro.json SAIDA/nome --modo ambos --previa
```

   - `--modo cor|pb|ambos` (padrão `ambos`).
   - `--enquadramento auto|preencher|ajustar`. `auto` preenche vídeos verticais. Vídeos horizontais entram inteiros no meio com fundo desfocado, para sobrar espaço para o texto sem cobrir o rosto.
   - Confira a saída: `frames com texto sobre o rosto: 0`. Se aparecer `AVISO: sem espaço livre`, rode de novo com `--enquadramento ajustar` ou encurte as linhas.

4. **Revisar a prévia** (`SAIDA/nome_previa_cor.png` e `_pb.png`, um frame por tela + frame final). Confira que o rosto está livre e que o texto está centralizado.

5. **Entregar**: o usuário prefere **receber a print (prévia)**, não o vídeo, a menos que peça o arquivo. Diga onde ficaram os MP4.

## Regras do usuário

- Nunca coloque texto ou elemento na frente do rosto.
- Texto o mais no meio da tela possível, sem cobrir o rosto.
- Ao pedirem uma variação, crie um arquivo novo. Não altere uma versão já aprovada.
- Respostas curtas e diretas, sem travessões nem ponto e vírgula.

## Ajustes finos

Constantes no topo de `scripts/reels_r7.py`: `SIZE` (80, texto), `CALL_SIZE` (58, chamada), `MARGEM_QUEIXO` (84 px), `LIMITE_BAIXO` (1680, evita a interface do Reels), cores e `FUNDOS`. O tamanho cai sozinho se uma linha não couber na largura ou se o bloco não couber abaixo do queixo.
