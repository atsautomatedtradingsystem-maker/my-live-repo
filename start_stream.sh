#!/usr/bin/env bash
set -euo pipefail

# Параметри відео — можеш змінити
WIDTH=${WIDTH:-1280}
HEIGHT=${HEIGHT:-720}
FPS=${FPS:-30}
VBITRATE=${VBITRATE:-2500k}
ABITRATE=${ABITRATE:-160k}

# Зчитати ключ з оточення
if [ -z "${YT_STREAM_KEY:-}" ]; then
  echo "ERROR: YT_STREAM_KEY is not set (set it in .env or pass as env var)"
  exit 1
fi

# display
export DISPLAY=:99

# стартуем Xvfb
Xvfb :99 -screen 0 ${WIDTH}x${HEIGHT}x24 >/tmp/xvfb.log 2>&1 &
sleep 1

# Запустити Dash app (live.py слухає на 8050)
# Якщо твій live.py приймає CLI опції — підкоригуй команду
python3 /app/live.py >/tmp/dash.log 2>&1 &

# почекай, щоб Dash піднявся
sleep 4

# Запустити chromium у віртуальному дисплеї, щоб рендерити UI
chromium-browser --no-sandbox --disable-gpu --window-size=${WIDTH},${HEIGHT} "http://127.0.0.1:8050" >/tmp/chrome.log 2>&1 &

sleep 2

# FFmpeg: хапаємо Xvfb (:99.0) та надсилаємо в два RTMP via tee (основний + резервний)
ffmpeg -y \
  -f x11grab -r ${FPS} -s ${WIDTH}x${HEIGHT} -i :99.0 \
  -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=44100 \
  -c:v libx264 -preset veryfast -b:v ${VBITRATE} -maxrate 3000k -bufsize 6000k -g $((FPS*2)) \
  -c:a aac -b:a ${ABITRATE} -ar 44100 \
  -f tee "[f=flv]rtmp://a.rtmp.youtube.com/live2/${YT_STREAM_KEY}|[f=flv]rtmp://b.rtmp.youtube.com/live2/${YT_STREAM_KEY}?backup=1"
