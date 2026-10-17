---
name: cortes-silencio
description: Corta silêncios, pausas longas e respirações de vídeos falados (Reels do @lucasmedeiros.ai) com ffmpeg, normaliza o volume para o Instagram e entrega o vídeo em 1080x1920. Use SEMPRE que o pedido envolver tirar silêncio, cortar pausas, cortar respiração, "jump cut", limpar a fala, "edita esse vídeo pra reels", deixar o vídeo mais dinâmico ou mais curto, ou quando um vídeo .mp4/.mov de fala for enviado para edição. Também é a primeira etapa obrigatória da edição com elementos gráficos (skill 2) e serve para limpar só o áudio (.wav/.m4a/.mp3) quando não houver vídeo.
---

# Cortes de silêncio

Remove do vídeo os trechos sem fala (pausas e respirações) e devolve um Reel limpo, no ritmo de jump cut. Tudo roda localmente com ffmpeg e um script Python.

## O que a skill entrega

- `<nome>_cortado.mp4`: vídeo 1080x1920, 30 fps, H.264, áudio AAC 48 kHz normalizado em -14 LUFS (padrão do Instagram)
- `<nome>_cortado_cortes.json`: relatório com duração antes e depois, lista de cada corte (início, fim, tipo) e os parâmetros usados. A skill 2 usa esse arquivo.

Se a entrada for só áudio, a saída é `<nome>_cortado.m4a`.

## Pré-requisitos (checar na primeira vez)

```bash
ffmpeg -version && python3 -c "import numpy"
```

Se faltar algo:
- Mac: `brew install ffmpeg` e `pip3 install numpy`
- Windows: `winget install Gyan.FFmpeg` e `pip install numpy`, depois fechar e abrir o terminal. No Windows o comando costuma ser `python` em vez de `python3`.

## Fluxo

1. **Analisar antes de renderizar.** Renderizar é a etapa lenta, então confirme o plano primeiro:
   ```bash
   python3 <pasta-da-skill>/scripts/cortar_silencios.py "VIDEO.mp4" --analisar
   ```
   Mostre ao Lucas: duração antes e depois, % removido, número de cortes e de respirações, e os avisos.

2. **Conferir se o plano faz sentido.** Sinais de problema:
   - mais de 50% removido em vídeo de fala contínua: provavelmente está cortando fala baixa
   - 0 respirações em vídeo longo gravado no celular: o limiar pode estar baixo demais
   - aviso de vídeo horizontal: perguntar se quer recorte central ou `--formato original`

3. **Renderizar.**
   ```bash
   python3 <pasta-da-skill>/scripts/cortar_silencios.py "VIDEO.mp4"
   ```
   Para conferir cortes rapidamente antes da versão final, use `--rapido` (qualidade menor, render mais rápido).

4. **Reportar** em poucas linhas: arquivo gerado, duração final, quantos cortes. Não precisa listar cada corte, o JSON tem isso.

Para vários vídeos, rode o comando em sequência para cada arquivo da pasta.

## Ajustes por sintoma

Os padrões foram escolhidos para soar natural. Só mude quando o Lucas reclamar de algo específico.

| Sintoma | Ajuste |
|---|---|
| Fala ficou corrida, sem respiro entre frases | `--min-silencio 0.4` ou `--margem 0.08` |
| Ainda sobram pausas | `--min-silencio 0.2` |
| Começo ou final de palavras cortado | `--margem 0.08` e `--faixa-db 40` |
| Respiração passou | `--faixa-db 26` (limiar mais alto) |
| Cortou "s" ou "f" no começo de palavra | `--resp-borda 0.4` |
| Quer manter as respirações | `--respiracoes manter` |
| Estalos nos cortes | `--fade 0.02` |
| Ambiente com ruído alto (ventilador, rua) | `--limiar-db` com valor entre o ruído e a fala, vistos no relatório em `niveis_db` |
| Quer manter o enquadramento horizontal | `--formato original` |
| Gravou em 60 fps e quer manter | `--fps 60` |

Sobre o limite de 0,1 s: é possível (`--min-silencio 0.1`), mas pausas entre palavras ficam entre 0,1 e 0,3 s e o resultado tende a soar robótico. Se o Lucas pedir, faça e avise para comparar com o padrão de 0,3 s.

## Como a detecção funciona (para diagnosticar)

O script mede o nível de fala e o piso de ruído de cada vídeo e define o limiar de silêncio de forma adaptativa (`faixa-db` abaixo da fala). Respirações têm energia, mas não têm vibração de cordas vocais. O script mede essa vibração (autocorrelação na faixa de 70 a 400 Hz) e trata como respiração o trecho sem voz, curto e mais baixo que a fala. Respirações coladas no início ou no fim de uma frase são aparadas quando o trecho surdo passa de `--resp-borda`.

Os cortes são alinhados aos quadros do vídeo, vídeo e áudio são montados em cadeias separadas (sem dessincronia acumulada, inclusive em vídeos de celular com fps variável) e cada trecho recebe um fade de 10 ms para evitar estalos.

## Limites conhecidos

- Não remove vícios de linguagem ("é...", "tipo") nem frases regravadas. Isso exige transcrição e fica para uma versão futura.
- Música de fundo no vídeo original confunde a detecção. Grave sem trilha e adicione depois.
- O volume final pode ficar até 1,5 LU abaixo de -14 quando a voz tem picos muito altos. Isso é proteção contra distorção, não erro.
