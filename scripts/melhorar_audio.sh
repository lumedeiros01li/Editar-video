#!/usr/bin/env bash
# Limpa o áudio e equilibra o volume de quem fala baixo.
# Uso: scripts/melhorar_audio.sh entrada.mp4 saida.mp4
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
AF="aresample=48000,\
highpass=f=80,\
arnndn=m=$DIR/models/std.rnnn:mix=0.9,\
afftdn=nr=10:nf=-45:tn=1,\
equalizer=f=250:t=q:w=1:g=-2,\
equalizer=f=3500:t=q:w=1.2:g=3,\
dynaudnorm=f=200:g=11:p=0.9:m=12:t=0.003,\
acompressor=threshold=-20dB:ratio=3:attack=10:release=150:makeup=2,\
loudnorm=I=-16:TP=-1.5:LRA=7,\
alimiter=limit=0.8,\
volume=-1.5dB,\
aresample=48000"
ffmpeg -y -i "$1" -map 0:v -map 0:a -c:v copy -af "$AF" -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$2"
