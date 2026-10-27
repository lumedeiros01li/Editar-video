#!/bin/sh
# Instala o que a skill precisa (uma vez por ambiente).
set -e
command -v ffmpeg >/dev/null || apt-get install -y ffmpeg
fc-list | grep -qi "Inter-SemiBold" || apt-get install -y fonts-inter
fc-list | grep -qi "DejaVuSansMono" || apt-get install -y fonts-dejavu-core
fc-list | grep -qi "NotoColorEmoji" || apt-get install -y fonts-noto-color-emoji
pip install -q faster-whisper pillow numpy
ffmpeg -hide_banner -filters 2>/dev/null | grep -q " ass " || { echo "ffmpeg sem libass (filtro ass)"; exit 1; }
echo "ok"
